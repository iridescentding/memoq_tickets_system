import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
import logging
from django.conf import settings
from django.template import Context, Template as DjangoTemplate # For Django template language
from django.utils import timezone

# Assuming models are in the same app or accessible via ..models
from memoq_ticket_system.models import NotificationTemplate, NotificationLog, CompanySSOProvider, User, Ticket, Company

logger = logging.getLogger(__name__)

# Helper to build context for templates
def build_notification_context(ticket=None, reply=None, user_actor=None, company=None, **kwargs):
    context = {
        'settings': settings, # Access to Django settings if needed in templates
        'site_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
    }
    if ticket:
        context['ticket'] = ticket
        context['ticket_url'] = f"{context['site_url']}/tickets/{ticket.id}" # Generic ticket URL
        if ticket.company and ticket.company.ticket_submission_url_slug and ticket.ticket_url_slug:
             # More specific company ticket URL if slugs are set up
            context['company_ticket_url'] = f"{context['site_url']}/{ticket.company.ticket_submission_url_slug}/{ticket.ticket_url_slug}"
        elif ticket.company and ticket.company.ticket_submission_url_slug: # Fallback to company ticket list
            context['company_ticket_url'] = f"{context['site_url']}/tickets?company_slug={ticket.company.ticket_submission_url_slug}"


    if reply:
        context['reply'] = reply
    if user_actor: # The user who performed the action leading to notification
        context['user_actor'] = user_actor
    if company:
        context['company'] = company
    
    context.update(kwargs) # Add any other custom context variables
    return context


class NotificationManager:
    @staticmethod
    def send_notification_by_event(event_type, context_data, target_company=None, target_user=None):
        """
        Sends notifications based on an event type and context.
        It will find relevant NotificationTemplates (global or company-specific)
        and dispatch them.

        Args:
            event_type (str): The event identifier (e.g., 'ticket_created').
            context_data (dict): Data to render templates (e.g., {'ticket': ticket_obj, 'user_actor': request.user}).
            target_company (Company, optional): The company associated with the event. For company-specific templates.
            target_user (User, optional): The specific user to notify (for email or direct messages if applicable).
                                         If None, might notify a group via webhook based on template.
        """
        templates_to_send = NotificationTemplate.objects.filter(event_type=event_type, is_active=True)
        
        if target_company:
            company_templates = templates_to_send.filter(company=target_company)
            global_templates = templates_to_send.filter(company__isnull=True)
            # Prioritize company-specific templates if they exist for the event and channel
            # This logic might need refinement based on how overrides should work
            processed_channels_for_company = set()
            final_templates = []

            for ct in company_templates:
                final_templates.append(ct)
                processed_channels_for_company.add(ct.channel)
            for gt in global_templates:
                if gt.channel not in processed_channels_for_company:
                    final_templates.append(gt)
            templates_to_send = final_templates
        else: # Only global templates if no target company
            templates_to_send = templates_to_send.filter(company__isnull=True)

        if not templates_to_send.exists():
            logger.info(f"No active notification templates found for event '{event_type}' (Company: {target_company.name if target_company else 'Global'}).")
            return

        for template_obj in templates_to_send:
            subject = DjangoTemplate(template_obj.subject_template).render(Context(context_data))
            body = DjangoTemplate(template_obj.body_template).render(Context(context_data))
            
            recipient_contact_info = None
            webhook_provider_config = None
            mentioned_platform_ids = [] # For @mentions

            if template_obj.channel == 'email':
                if target_user and target_user.email and target_user.notification_config.email_enabled:
                    recipient_contact_info = target_user.email
                elif 'default_email_recipient' in context_data: # e.g. for support group email
                    recipient_contact_info = context_data['default_email_recipient']
                else:
                    logger.warning(f"Email template '{template_obj.name}' for event '{event_type}' has no target user email or default recipient.")
                    continue
            
            elif template_obj.channel in ['feishu', 'enterprise_wechat']:
                if not target_company:
                    logger.warning(f"Webhook template '{template_obj.name}' for channel '{template_obj.channel}' requires a target company.")
                    continue
                try:
                    webhook_provider_config = CompanySSOProvider.objects.get(
                        company=target_company, 
                        provider_type=template_obj.channel, # Assuming channel name matches provider_type
                        is_enabled=True
                    )
                    recipient_contact_info = webhook_provider_config.webhook_url
                    if not recipient_contact_info:
                        logger.warning(f"{template_obj.channel.capitalize()} webhook URL not configured for company '{target_company.name}'.")
                        continue
                    
                    # Prepare @mentions - context_data should contain users to be mentioned
                    # Example: if 'ticket_creator_user' in context_data and it's a User object
                    user_to_mention = context_data.get('ticket_creator_user') # Or 'assigned_user', etc.
                    if user_to_mention and isinstance(user_to_mention, User):
                        if template_obj.channel == 'feishu' and user_to_mention.feishu_id:
                            mentioned_platform_ids.append(user_to_mention.feishu_id)
                        elif template_obj.channel == 'enterprise_wechat' and user_to_mention.enterprise_wechat_id:
                            mentioned_platform_ids.append(user_to_mention.enterprise_wechat_id)

                except CompanySSOProvider.DoesNotExist:
                    logger.warning(f"No active {template_obj.channel.capitalize()} SSO/Webhook config found for company '{target_company.name}'.")
                    continue
            else:
                logger.warning(f"Unsupported notification channel: {template_obj.channel}")
                continue

            # Log before sending
            log_entry = NotificationLog.objects.create(
                user=context_data.get('user_actor'), # User who triggered the event
                company=target_company,
                ticket=context_data.get('ticket'),
                notification_type=template_obj.channel,
                recipient_info=str(recipient_contact_info)[:250], # Truncate if too long
                content_summary=subject,
                status='pending'
            )

            try:
                success = NotificationManager._dispatch_send(
                    channel=template_obj.channel,
                    recipient_contact_info=recipient_contact_info,
                    subject=subject,
                    body=body, # This is the rendered body
                    mentioned_user_ids=mentioned_platform_ids,
                    # Pass company's general email config if it's an email
                    email_config=target_company.email_config if target_company and template_obj.channel == 'email' else None
                )
                log_entry.status = 'sent' if success else 'failed'
            except Exception as e:
                logger.error(f"Error dispatching notification for template '{template_obj.name}': {e}")
                log_entry.status = 'failed'
                log_entry.response_info = str(e)
            
            log_entry.sent_at = timezone.now() if log_entry.status == 'sent' else None
            log_entry.save()


    @staticmethod
    def _dispatch_send(channel, recipient_contact_info, subject, body, mentioned_user_ids=None, email_config=None):
        """Internal method to call specific senders."""
        if channel == 'email':
            # Use company-specific email_config if provided, else global Django settings
            smtp_server = email_config.get('smtp_server') if email_config else settings.EMAIL_HOST
            smtp_port = email_config.get('smtp_port') if email_config else settings.EMAIL_PORT
            from_address = email_config.get('from_email') if email_config else settings.DEFAULT_FROM_EMAIL
            from_name = email_config.get('from_name', "MemoQ Ticket System") if email_config else "MemoQ Ticket System"
            # Add logic for SMTP user/pass from email_config if they exist
            
            return NotificationManager.send_email(
                recipient_contact_info, subject, body, # Body is HTML for email
                smtp_server, smtp_port, from_address, from_name
            )
        elif channel == 'enterprise_wechat':
            return NotificationManager.send_enterprise_wechat(
                recipient_contact_info, subject, body, # Body is Markdown for WeCom
                mentioned_user_ids=mentioned_user_ids
            )
        elif channel == 'feishu':
            return NotificationManager.send_feishu(
                recipient_contact_info, subject, body, # Body is Markdown for Feishu Card
                mentioned_user_ids=mentioned_user_ids
            )
        # Add other channels
        return False

    @staticmethod
    def send_email(recipient_email, subject, html_content, smtp_server, smtp_port, from_address, from_name):
        # ... (Existing logic - ensure it uses provided smtp_server etc.) ...
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_address}>"
            msg["To"] = recipient_email
            msg.attach(MIMEText(html_content, "html")) # Assuming body is HTML

            # Use global Django settings for auth if not in company_email_config
            smtp_user = getattr(settings, 'EMAIL_HOST_USER', None)
            smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            use_tls = getattr(settings, 'EMAIL_USE_TLS', True)


            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls: # Check settings or company_config
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            logger.info(f"邮件已发送至 {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"发送邮件失败 for {recipient_email}: {str(e)}")
            return False


    @staticmethod
    def send_enterprise_wechat(webhook_url, subject, markdown_body, mentioned_user_ids=None):
        # ... (Existing logic, ensure markdown_body and mentioned_user_ids are used correctly) ...
        if not webhook_url:
            logger.error("企业微信Webhook URL未配置")
            return False
        try:
            # Subject can be part of the markdown_body for WeCom
            final_markdown_content = f"### {subject}\n\n{markdown_body}"
            
            payload = {
                "msgtype": "markdown",
                "markdown": { "content": final_markdown_content }
            }
            
            if mentioned_user_ids and isinstance(mentioned_user_ids, list):
                mention_str = " ".join([f"<@{uid}>" for uid in mentioned_user_ids if uid])
                if mention_str: # Only add if there are valid mentions
                    payload["markdown"]["content"] = f"{final_markdown_content}\n{mention_str}"
                    payload["markdown"]["mentioned_list"] = [uid for uid in mentioned_user_ids if uid]
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response_data = response.json()
            if response.status_code == 200 and response_data.get("errcode") == 0:
                logger.info(f"企业微信通知已发送至 {webhook_url}")
                return True
            else:
                logger.error(f"发送企业微信通知失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"发送企业微信通知异常: {str(e)}")
            return False

    @staticmethod
    def send_feishu(webhook_url, subject, markdown_body, mentioned_user_ids=None):
        # ... (Existing logic, ensure markdown_body and mentioned_user_ids are used for Feishu card) ...
        if not webhook_url:
            logger.error("飞书Webhook URL未配置")
            return False
        try:
            lark_md_content = markdown_body # Use the rendered markdown body

            if mentioned_user_ids and isinstance(mentioned_user_ids, list):
                mentions_text = " ".join([f'<at user_id="{uid}"></at>' for uid in mentioned_user_ids if uid])
                if mentions_text: # Only add if there are valid mentions
                    lark_md_content += f"\n\n{mentions_text}" 

            payload = {
                "msg_type": "interactive",
                "card": {
                    "config": {"wide_screen_mode": True},
                    "header": {"title": {"tag": "plain_text", "content": subject}, "template": "blue"},
                    "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": lark_md_content}}]
                }
            }
            response = requests.post(webhook_url, json=payload, timeout=10)
            response_data = response.json()
            if response.status_code == 200 and response_data.get("StatusCode") == 0:
                logger.info(f"飞书通知已发送至 {webhook_url}")
                return True
            else:
                logger.error(f"发送飞书通知失败: {response.status_code} - {response.text}, Response Data: {response_data}")
                return False
        except Exception as e:
            logger.error(f"发送飞书通知异常: {str(e)}")
            return False

# Example of how signals.py would change to use send_notification_by_event:
# @receiver(post_save, sender=Ticket)
# def ticket_creation_signal_handler(sender, instance, created, **kwargs):
#     if created:
#         ticket = instance
#         context = build_notification_context(
#             ticket=ticket,
#             user_actor=ticket.created_by, # User who created the ticket
#             company=ticket.company,
#             # Add any other relevant context for templates
#             ticket_creator_user=ticket.created_by # Specifically for @mentioning the creator
#         )
#         # Notify the ticket creator (e.g., via email)
#         if ticket.created_by:
#              NotificationManager.send_notification_by_event(
#                 event_type='ticket_created', # Corresponds to NotificationTemplate.event_type
#                 context_data=context,
#                 target_user=ticket.created_by, # For direct email
#                 target_company=ticket.company # For company specific templates/configs
#             )
#         # Notify support group (e.g., via Feishu to a group webhook)
#         # The template for 'ticket_created' and channel 'feishu' should be configured
#         # to go to a specific group webhook URL (stored in CompanySSOProvider.webhook_url).
#         # No specific target_user needed if it's a group message, but context can include users to @mention.
#         NotificationManager.send_notification_by_event(
#             event_type='ticket_created',
#             context_data=context, # Context might include assigned_to for mentions if assigned at creation
#             target_company=ticket.company # Essential for getting company's Feishu webhook
#         )