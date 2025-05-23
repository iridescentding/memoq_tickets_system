from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket, TicketReply, NotificationLog
from .notifications import NotificationManager
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Ticket)
def ticket_notification_handler(sender, instance, created, **kwargs):
    """
    处理工单创建和更新的通知
    """
    try:
        # 获取相关对象
        ticket = instance
        company = ticket.company
        created_by = ticket.created_by
        assigned_to = ticket.assigned_to

        # 记录通知日志
        notification_log = NotificationLog(
            user=created_by,
            ticket=ticket,
            notification_type=(
                "ticket_status_change" if not created else "ticket_created"
            ),
        )

        if created:
            # 工单创建通知
            # 1. 通知技术支持团队
            subject = f"新工单 #{ticket.id}: {ticket.title}"
            content = f"""
            <h2>新工单已创建</h2>
            <p><strong>工单号:</strong> #{ticket.id}</p>
            <p><strong>标题:</strong> {ticket.title}</p>
            <p><strong>公司:</strong> {company.name}</p>
            <p><strong>优先级:</strong> {ticket.get_priority_display()}</p>
            <p><strong>创建者:</strong> {created_by.username}</p>
            <p><strong>描述:</strong> {ticket.description[:200]}...</p>
            <p><a href="{get_ticket_url(ticket.id)}">点击查看工单详情</a></p>
            """

            # 获取所有技术支持人员的邮箱
            from .models import User

            support_emails = User.objects.filter(role="support").values_list(
                "email", flat=True
            )

            for email in support_emails:
                NotificationManager.send_notification(
                    "email", email, subject, content, ticket=ticket, company=company
                )

            # 2. 通知客户工单已创建
            customer_subject = f"您的工单 #{ticket.id} 已创建"
            customer_content = f"""
            <h2>您的工单已成功创建</h2>
            <p><strong>工单号:</strong> #{ticket.id}</p>
            <p><strong>标题:</strong> {ticket.title}</p>
            <p><strong>优先级:</strong> {ticket.get_priority_display()}</p>
            <p><strong>描述:</strong> {ticket.description[:200]}...</p>
            <p>我们的技术支持团队将尽快处理您的工单。</p>
            <p><a href="{get_ticket_url(ticket.id)}">点击查看工单详情</a></p>
            """

            # 根据客户选择的联系方式发送通知
            if ticket.contact_method == "email":
                NotificationManager.send_notification(
                    "email",
                    ticket.contact_info,
                    customer_subject,
                    customer_content,
                    ticket=ticket,
                    company=company,
                )
            elif ticket.contact_method == "wechat":
                NotificationManager.send_notification(
                    "wechat",
                    ticket.contact_info,
                    customer_subject,
                    customer_content,
                    ticket=ticket,
                    company=company,
                )
            elif ticket.contact_method == "enterprise_wechat":
                NotificationManager.send_notification(
                    "enterprise_wechat",
                    ticket.contact_info,
                    customer_subject,
                    customer_content,
                    ticket=ticket,
                    company=company,
                )
            elif ticket.contact_method == "feishu":
                NotificationManager.send_notification(
                    "feishu",
                    ticket.contact_info,
                    customer_subject,
                    customer_content,
                    ticket=ticket,
                    company=company,
                )

            notification_log.message = f"工单创建通知已发送"

        else:
            # 工单更新通知
            # 检查状态是否变更
            if (
                hasattr(instance, "_original_status")
                and instance._original_status != instance.status
            ):
                # 状态变更通知
                status_subject = (
                    f"工单 #{ticket.id} 状态已更新: {ticket.get_status_display()}"
                )
                status_content = f"""
                <h2>工单状态已更新</h2>
                <p><strong>工单号:</strong> #{ticket.id}</p>
                <p><strong>标题:</strong> {ticket.title}</p>
                <p><strong>新状态:</strong> {ticket.get_status_display()}</p>
                <p><strong>更新者:</strong> {ticket.updated_by.username if ticket.updated_by else '系统'}</p>
                <p><a href="{get_ticket_url(ticket.id)}">点击查看工单详情</a></p>
                """

                # 通知客户
                if ticket.contact_method == "email":
                    NotificationManager.send_notification(
                        "email",
                        ticket.contact_info,
                        status_subject,
                        status_content,
                        ticket=ticket,
                        company=company,
                    )
                elif ticket.contact_method == "wechat":
                    NotificationManager.send_notification(
                        "wechat",
                        ticket.contact_info,
                        status_subject,
                        status_content,
                        ticket=ticket,
                        company=company,
                    )
                elif ticket.contact_method == "enterprise_wechat":
                    NotificationManager.send_notification(
                        "enterprise_wechat",
                        ticket.contact_info,
                        status_subject,
                        status_content,
                        ticket=ticket,
                        company=company,
                    )
                elif ticket.contact_method == "feishu":
                    NotificationManager.send_notification(
                        "feishu",
                        ticket.contact_info,
                        status_subject,
                        status_content,
                        ticket=ticket,
                        company=company,
                    )

                # 如果有分配的技术支持，也通知他们
                if assigned_to and assigned_to.email:
                    NotificationManager.send_notification(
                        "email",
                        assigned_to.email,
                        status_subject,
                        status_content,
                        ticket=ticket,
                        company=company,
                    )

                notification_log.message = (
                    f"工单状态更新通知已发送: {ticket.get_status_display()}"
                )

            # 检查分配是否变更
            if (
                hasattr(instance, "_original_assigned_to")
                and instance._original_assigned_to != instance.assigned_to
            ):
                # 分配变更通知
                if assigned_to:
                    assign_subject = f"工单 #{ticket.id} 已分配给您"
                    assign_content = f"""
                    <h2>工单已分配给您</h2>
                    <p><strong>工单号:</strong> #{ticket.id}</p>
                    <p><strong>标题:</strong> {ticket.title}</p>
                    <p><strong>公司:</strong> {company.name}</p>
                    <p><strong>优先级:</strong> {ticket.get_priority_display()}</p>
                    <p><strong>状态:</strong> {ticket.get_status_display()}</p>
                    <p><a href="{get_ticket_url(ticket.id)}">点击查看工单详情</a></p>
                    """

                    NotificationManager.send_notification(
                        "email",
                        assigned_to.email,
                        assign_subject,
                        assign_content,
                        ticket=ticket,
                        company=company,
                    )

                    notification_log.message = (
                        f"工单分配通知已发送给: {assigned_to.username}"
                    )

        notification_log.save()

    except Exception as e:
        logger.error(f"发送工单通知失败: {str(e)}")


@receiver(post_save, sender=TicketReply)
def reply_notification_handler(sender, instance, created, **kwargs):
    """
    处理工单回复的通知
    """
    if not created:
        # 只处理新创建的回复
        return

    try:
        # 获取相关对象
        reply = instance
        ticket = reply.ticket
        company = ticket.company
        user = reply.user

        # 如果是内部备注，不发送通知给客户
        if reply.is_internal:
            # 只通知技术支持团队
            if user.role != "support" and user.role != "admin":
                return

            subject = f"工单 #{ticket.id} 有新的内部备注"
            content = f"""
            <h2>工单有新的内部备注</h2>
            <p><strong>工单号:</strong> #{ticket.id}</p>
            <p><strong>标题:</strong> {ticket.title}</p>
            <p><strong>备注者:</strong> {user.username}</p>
            <p><strong>备注内容:</strong> {reply.content[:200]}...</p>
            <p><a href="{get_ticket_url(ticket.id)}">点击查看工单详情</a></p>
            """

            # 获取所有技术支持人员的邮箱
            from .models import User

            support_emails = User.objects.filter(
                role__in=["support", "admin"]
            ).values_list("email", flat=True)

            for email in support_emails:
                if email != user.email:  # 不发送给备注者自己
                    NotificationManager.send_notification(
                        "email", email, subject, content, ticket=ticket, company=company
                    )

            # 记录通知日志
            NotificationLog.objects.create(
                user=user,
                ticket=ticket,
                notification_type="internal_note",
                message="内部备注通知已发送给技术支持团队",
            )

        else:
            # 普通回复，通知相关人员
            subject = f"工单 #{ticket.id} 有新回复"
            content = f"""
            <h2>工单有新回复</h2>
            <p><strong>工单号:</strong> #{ticket.id}</p>
            <p><strong>标题:</strong> {ticket.title}</p>
            <p><strong>回复者:</strong> {user.username}</p>
            <p><strong>回复内容:</strong> {reply.content[:200]}...</p>
            <p><a href="{get_ticket_url(ticket.id)}">点击查看工单详情</a></p>
            """

            # 如果回复者是客户，通知技术支持团队
            if user.role == "customer":
                # 获取所有技术支持人员的邮箱
                from .models import User

                support_emails = User.objects.filter(
                    role__in=["support", "admin"]
                ).values_list("email", flat=True)

                for email in support_emails:
                    NotificationManager.send_notification(
                        "email", email, subject, content, ticket=ticket, company=company
                    )

                # 记录通知日志
                NotificationLog.objects.create(
                    user=user,
                    ticket=ticket,
                    notification_type="customer_reply",
                    message="客户回复通知已发送给技术支持团队",
                )

            # 如果回复者是技术支持，通知客户
            elif user.role in ["support", "admin"]:
                # 根据客户选择的联系方式发送通知
                if ticket.contact_method == "email":
                    NotificationManager.send_notification(
                        "email",
                        ticket.contact_info,
                        subject,
                        content,
                        ticket=ticket,
                        company=company,
                    )
                elif ticket.contact_method == "wechat":
                    NotificationManager.send_notification(
                        "wechat",
                        ticket.contact_info,
                        subject,
                        content,
                        ticket=ticket,
                        company=company,
                    )
                elif ticket.contact_method == "enterprise_wechat":
                    NotificationManager.send_notification(
                        "enterprise_wechat",
                        ticket.contact_info,
                        subject,
                        content,
                        ticket=ticket,
                        company=company,
                    )
                elif ticket.contact_method == "feishu":
                    NotificationManager.send_notification(
                        "feishu",
                        ticket.contact_info,
                        subject,
                        content,
                        ticket=ticket,
                        company=company,
                    )

                # 记录通知日志
                NotificationLog.objects.create(
                    user=user,
                    ticket=ticket,
                    notification_type="support_reply",
                    message="技术支持回复通知已发送给客户",
                )

    except Exception as e:
        logger.error(f"发送回复通知失败: {str(e)}")


def get_ticket_url(ticket_id):
    """
    生成工单详情页面的URL
    """
    from django.conf import settings

    base_url = getattr(settings, "FRONTEND_URL", "http://localhost:8080")
    return f"{base_url}/tickets/{ticket_id}"
