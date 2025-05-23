from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone

from memoq_ticket_system.models import (
    Company, CompanyConfig, Ticket, TicketReply, TicketStatusHistory,
    NotificationConfig, NotificationLog, Attachment, CustomerTypeTag,
    TicketType, TicketLabel, TicketTransferHistory,
    CompanySSOProvider, NotificationTemplate, TicketSatisfactionRating # New models
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True, allow_null=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "wechat_id", "feishu_id", "enterprise_wechat_id",
            "company", "company_name", "role", "role_display",
            "is_active", "date_joined", "is_deleted", "deleted_at" # Added soft delete fields
        ]
        read_only_fields = ["date_joined", "role_display", "deleted_at"]
        extra_kwargs = {
            "password": {"write_only": True, "required": False}, # Not required for updates
            "is_deleted": {"read_only": True} # is_deleted should be handled by methods
        }

    def create(self, validated_data):
        # company can be None for support staff/admins
        company = validated_data.pop('company', None)
        user = User.objects.create_user(**validated_data)
        if company:
            user.company = company
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        # Prevent role escalation for non-system admins or self-escalation
        current_user = self.context['request'].user
        if 'role' in validated_data and instance.pk == current_user.pk and instance.role != validated_data['role']:
             if not current_user.is_superuser and current_user.role != User.ROLE_SYSTEM_ADMIN : # Allow superuser to change any role
                raise serializers.ValidationError("您不能更改自己的角色。")
        if 'role' in validated_data and not current_user.is_superuser and current_user.role != User.ROLE_SYSTEM_ADMIN:
             if validated_data['role'] == User.ROLE_SYSTEM_ADMIN and instance.role != User.ROLE_SYSTEM_ADMIN :
                 raise serializers.ValidationError("您没有权限将用户设置成系统管理员。")

        return super().update(instance, validated_data)

class CustomerTypeTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTypeTag
        fields = ["id", "name"]

class CompanySSOProviderSerializer(serializers.ModelSerializer):
    provider_type_display = serializers.CharField(source="get_provider_type_display", read_only=True)
    class Meta:
        model = CompanySSOProvider
        fields = [
            "id", "company", "provider_type", "provider_type_display", "is_enabled",
            "app_id", "app_secret", "agent_id", "webhook_url", "additional_config",
            "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at", "provider_type_display"]
        extra_kwargs = {
            "company": {"write_only": True, "required": False} # Usually set implicitly or via nested write
        }

class CompanySerializer(serializers.ModelSerializer):
    customer_types_display = CustomerTypeTagSerializer(source="customer_types", many=True, read_only=True)
    customer_types = serializers.PrimaryKeyRelatedField(queryset=CustomerTypeTag.objects.all(), many=True, write_only=True, required=False)
    logo_url = serializers.SerializerMethodField()
    login_background_url = serializers.SerializerMethodField()
    sso_providers = CompanySSOProviderSerializer(many=True, read_only=True) # Read related SSO configs

    class Meta:
        model = Company
        fields = [
            "id", "name", "code", "contact_person", "contact_email", "contact_phone",
            "is_active", "customer_types", "customer_types_display",
            "professional_services", "logo", "logo_url", "login_background", "login_background_url",
            "products", "importance", "ticket_submission_url_slug", "email_config",
            "default_sso_provider_type", "sso_providers", # Display configured providers
            "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at", "sso_providers"]
        extra_kwargs = {
            "logo": {"write_only": True, "required": False},
            "login_background": {"write_only": True, "required": False},
        }

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_login_background_url(self, obj):
        request = self.context.get('request')
        if obj.login_background and request:
            return request.build_absolute_uri(obj.login_background.url)
        return None

    def validate_default_sso_provider_type(self, value):
        if value: # If a default is chosen
            # Ensure this provider type is one of the enabled ones for the company
            # This validation is tricky here as sso_providers are related objects
            # Better to do this validation at the view level or CompanySSOProvider model save
            pass
        return value

    def create(self, validated_data):
        customer_types_data = validated_data.pop('customer_types', [])
        company = Company.objects.create(**validated_data)
        if customer_types_data:
            company.customer_types.set(customer_types_data)
        return company

    def update(self, instance, validated_data):
        customer_types_data = validated_data.pop('customer_types', None)
        instance = super().update(instance, validated_data)
        if customer_types_data is not None:
            instance.customer_types.set(customer_types_data)
        return instance


class CompanyConfigSerializer(serializers.ModelSerializer):
    # ... (Existing serializer, likely no changes needed unless SLA depends on new fields)
    class Meta:
        model = CompanyConfig
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    # ... (Existing serializer)
    file_url = serializers.FileField(source="file", read_only=True, use_url=True)
    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True, allow_null=True)

    class Meta:
        model = Attachment
        fields = ["id", "file_name", "file", "file_url", "file_size", "file_type",
                  "ticket", "reply", "uploaded_by", "uploaded_by_username", "created_at"]
        read_only_fields = ["file_size", "file_type", "created_at", "file_url", "uploaded_by_username"]
        extra_kwargs = {"file": {"write_only": True}}

    def create(self, validated_data):
        file_obj = validated_data.get("file")
        if file_obj:
            validated_data["file_size"] = file_obj.size
            validated_data["file_type"] = file_obj.content_type
            if not validated_data.get("file_name"):
                validated_data["file_name"] = file_obj.name
        return super().create(validated_data)


class TicketReplySerializer(serializers.ModelSerializer):
    attachments_data = AttachmentSerializer(source="attachments", many=True, read_only=True)
    user_info = UserSerializer(source="user", read_only=True)

    class Meta:
        model = TicketReply
        fields = [
            "id", "ticket", "user", "user_info", "content", "is_internal",
            "created_at", "updated_at", "email_sent", "email_sent_at", "attachments_data"
        ]
        read_only_fields = ["created_at", "updated_at", "user_info", "attachments_data", "email_sent", "email_sent_at"]
        extra_kwargs = {"user": {"write_only": True, "required": False}}

class TicketStatusHistorySerializer(serializers.ModelSerializer):
    # ... (Existing serializer)
    changed_by_username = serializers.CharField(source="changed_by.username", read_only=True, allow_null=True)
    old_status_display = serializers.CharField(source="get_old_status_display", read_only=True)
    new_status_display = serializers.CharField(source="get_new_status_display", read_only=True)

    class Meta:
        model = TicketStatusHistory
        fields = ["id", "ticket", "changed_by", "changed_by_username",
                  "old_status", "old_status_display", "new_status", "new_status_display",
                  "reason", "created_at"]
        read_only_fields = ["created_at", "changed_by_username", "old_status_display", "new_status_display"]


class TicketTypeSerializer(serializers.ModelSerializer):
    # ... (Existing serializer)
    parent_name = serializers.CharField(source="parent.name", read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, allow_null=True)
    class Meta:
        model = TicketType
        fields = ["id", "name", "description", "parent", "parent_name",
                  "created_by", "created_by_username", "created_at", "updated_at", "is_active", "level"]
        read_only_fields = ["created_at", "updated_at", "parent_name", "created_by_username", "level"]


class TicketLabelSerializer(serializers.ModelSerializer):
    # ... (Existing serializer)
    class Meta:
        model = TicketLabel
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]

class TicketTransferHistorySerializer(serializers.ModelSerializer):
    # ... (Existing serializer)
    transferred_by_username = serializers.CharField(source="transferred_by.username", read_only=True, allow_null=True)
    transferred_from_username = serializers.CharField(source="transferred_from.username", read_only=True, allow_null=True)
    transferred_to_username = serializers.CharField(source="transferred_to.username", read_only=True, allow_null=True)
    class Meta:
        model = TicketTransferHistory
        fields = ["id", "ticket", "transferred_by", "transferred_by_username",
                  "transferred_from", "transferred_from_username",
                  "transferred_to", "transferred_to_username", "reason", "created_at"]
        read_only_fields = ["created_at", "transferred_by_username", "transferred_from_username", "transferred_to_username"]


class TicketSatisfactionRatingSerializer(serializers.ModelSerializer):
    rated_by_username = serializers.CharField(source="rated_by.username", read_only=True, allow_null=True)
    rating_display = serializers.CharField(source="get_rating_display", read_only=True)

    class Meta:
        model = TicketSatisfactionRating
        fields = [
            "id", "ticket", "rated_by", "rated_by_username",
            "rating", "rating_display", "comment", "created_at"
        ]
        read_only_fields = ["created_at", "rated_by_username", "rating_display"]
        extra_kwargs = {
            "rated_by": {"required": False} # Should be set to request.user if customer
        }

class TicketSerializer(serializers.ModelSerializer):
    company_details = CompanySerializer(source="company", read_only=True)
    created_by_details = UserSerializer(source="created_by", read_only=True)
    submitted_by_details = UserSerializer(source="submitted_by", read_only=True)
    assigned_to_details = UserSerializer(source="assigned_to", read_only=True, allow_null=True)

    replies_data = TicketReplySerializer(source="replies", many=True, read_only=True)
    status_history_data = TicketStatusHistorySerializer(source="status_history", many=True, read_only=True)
    attachments_data = AttachmentSerializer(source="attachments", many=True, read_only=True)

    ticket_type_details = TicketTypeSerializer(source="ticket_type", read_only=True, allow_null=True)
    labels_data = TicketLabelSerializer(source="labels", many=True, read_only=True)
    followers_data = UserSerializer(source="followers", many=True, read_only=True)
    transfer_history_data = TicketTransferHistorySerializer(source="transfer_history", many=True, read_only=True)
    satisfaction_rating_data = TicketSatisfactionRatingSerializer(source="satisfaction_rating", read_only=True, allow_null=True)


    status_display = serializers.CharField(source="get_status_display", read_only=True)
    urgency_display = serializers.CharField(source="get_urgency_display", read_only=True)
    contact_method_display = serializers.CharField(source="get_contact_method_display", read_only=True)
    closing_reason_type_display = serializers.CharField(source="get_closing_reason_type_display", read_only=True, allow_null=True)

    # SLA fields (read-only, calculated by model or signals/tasks)
    sla_ir_deadline_display = serializers.DateTimeField(source="sla_ir_deadline", read_only=True, format="%Y-%m-%d %H:%M")
    sla_resolution_deadline_display = serializers.DateTimeField(source="sla_resolution_deadline", read_only=True, format="%Y-%m-%d %H:%M")
    
    # Time remaining for SLA (calculated in to_representation)
    sla_ir_time_remaining = serializers.SerializerMethodField()
    sla_resolution_time_remaining = serializers.SerializerMethodField()
    is_ir_sla_missed = serializers.SerializerMethodField()
    is_resolution_sla_missed = serializers.SerializerMethodField()


    class Meta:
        model = Ticket
        fields = [
            "id", "title", "description",
            "company", "company_details",
            "created_by", "created_by_details",
            "submitted_by", "submitted_by_details",
            "assigned_to", "assigned_to_details",
            "status", "status_display",
            "priority", "urgency", "urgency_display",
            "category", "subcategory",
            "contact_method", "contact_method_display", "contact_info",
            "created_at", "updated_at", "last_activity_at",
            "first_replied_at", "last_customer_reply_at", "last_support_reply_at",
            "resolved_at", "closed_at",
            "paused_at", "pause_reason",
            "closing_reason_type", "closing_reason_type_display", "closing_reason_detail",
            "ticket_type", "ticket_type_details",
            "labels", "labels_data",
            "followers", "followers_data",
            "ticket_url_slug",
            "replies_data", "status_history_data", "attachments_data", "transfer_history_data",
            "satisfaction_rating_data", # New
            "sla_ir_deadline", "sla_resolution_deadline", # Raw deadlines
            "sla_ir_deadline_display", "sla_resolution_deadline_display", # Formatted
            "sla_ir_time_remaining", "sla_resolution_time_remaining",
            "is_ir_sla_missed", "is_resolution_sla_missed"

        ]
        read_only_fields = [
            "created_at", "updated_at", "last_activity_at", "first_replied_at",
            "last_customer_reply_at", "last_support_reply_at",
            "resolved_at", "closed_at", "paused_at", "status_display", "urgency_display",
            "contact_method_display", "closing_reason_type_display",
            "company_details", "created_by_details", "submitted_by_details", "assigned_to_details",
            "ticket_type_details", "labels_data", "followers_data",
            "replies_data", "status_history_data", "attachments_data", "transfer_history_data",
            "satisfaction_rating_data",
            "sla_ir_deadline", "sla_resolution_deadline", # These are set by model logic
            "sla_ir_deadline_display", "sla_resolution_deadline_display",
            "sla_ir_time_remaining", "sla_resolution_time_remaining",
            "is_ir_sla_missed", "is_resolution_sla_missed"
        ]
        extra_kwargs = {
            "company": {"write_only": True, "required": True},
            "created_by": {"write_only": True, "required": False}, # Set by request.user usually
            "submitted_by": {"write_only": True, "required": False},
            "assigned_to": {"write_only": True, "allow_null": True, "required": False},
            "ticket_type": {"write_only": True, "allow_null": True, "required": False},
            "labels": {"write_only": True, "required": False},
            "followers": {"write_only": True, "required": False},
            "ticket_url_slug": {"required": False, "allow_blank": True},
        }

    def _get_time_remaining(self, deadline):
        if deadline:
            now = timezone.now()
            if deadline > now:
                return (deadline - now).total_seconds()
            return - (now - deadline).total_seconds() # Negative for overdue
        return None

    def get_sla_ir_time_remaining(self, obj):
        return self._get_time_remaining(obj.sla_ir_deadline)

    def get_sla_resolution_time_remaining(self, obj):
        return self._get_time_remaining(obj.sla_resolution_deadline)

    def get_is_ir_sla_missed(self, obj):
        if obj.sla_ir_deadline and obj.first_replied_at: # Replied
            return obj.first_replied_at > obj.sla_ir_deadline
        elif obj.sla_ir_deadline and not obj.first_replied_at: # Not replied yet
            return timezone.now() > obj.sla_ir_deadline
        return False # No deadline or not applicable

    def get_is_resolution_sla_missed(self, obj):
        if obj.sla_resolution_deadline and obj.resolved_at: # Resolved
            return obj.resolved_at > obj.sla_resolution_deadline
        elif obj.sla_resolution_deadline and not obj.resolved_at: # Not resolved yet
            return timezone.now() > obj.sla_resolution_deadline
        return False # No deadline or not applicable


    def validate(self, data):
        ticket_type = data.get('ticket_type')
        if ticket_type and not ticket_type.is_leaf_node():
            raise serializers.ValidationError({"ticket_type": "工单类型必须选择最底层节点。"})
        # ... (slug generation logic if needed, or handle in model.save)
        return data

class NotificationTemplateSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True, allow_null=True)
    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)

    class Meta:
        model = NotificationTemplate
        fields = [
            "id", "name", "company", "company_name", "event_type", "event_type_display",
            "channel", "channel_display", "is_active", "subject_template", "body_template",
            "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at", "company_name", "event_type_display", "channel_display"]

# ... (Other existing serializers: TicketAssignmentSerializer, etc. should be reviewed for compatibility)

class AdminTicketDashboardSerializer(serializers.ModelSerializer):
    # ... (Existing serializer, might need to add SLA status) ...
    company_name = serializers.CharField(source="company.name", read_only=True)
    submitted_by_username = serializers.CharField(source="submitted_by.username", read_only=True, allow_null=True)
    urgency_display = serializers.CharField(source="get_urgency_display", read_only=True)
    sla_response_minutes = serializers.IntegerField(source="company.config.sla_response_minutes", read_only=True, allow_null=True)
    ticket_type_name = serializers.CharField(source="ticket_type.name", read_only=True, allow_null=True)
    labels_list = serializers.SerializerMethodField()

    is_ir_sla_missed = serializers.SerializerMethodField()
    is_resolution_sla_missed = serializers.SerializerMethodField()


    def get_labels_list(self, obj):
        return [{"id": label.id, "name": label.name, "color": label.color} for label in obj.labels.all()]

    def get_is_ir_sla_missed(self, obj):
        if obj.sla_ir_deadline and obj.first_replied_at: return obj.first_replied_at > obj.sla_ir_deadline
        elif obj.sla_ir_deadline: return timezone.now() > obj.sla_ir_deadline
        return False

    def get_is_resolution_sla_missed(self, obj):
        if obj.sla_resolution_deadline and obj.resolved_at: return obj.resolved_at > obj.sla_resolution_deadline
        elif obj.sla_resolution_deadline: return timezone.now() > obj.sla_resolution_deadline
        return False

    class Meta:
        model = Ticket
        fields = [
            "id", "title", "company_name", "submitted_by_username",
            "urgency_display", "priority", "created_at", "status",
            "sla_response_minutes", "ticket_type_name", "labels_list",
            "ticket_url_slug", "first_replied_at", "resolved_at",
            "sla_ir_deadline", "sla_resolution_deadline",
            "is_ir_sla_missed", "is_resolution_sla_missed"
        ]

class NotificationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationConfig
        fields = "__all__"

class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = "__all__"


class TicketAssignmentSerializer(serializers.Serializer):
    assigned_to_id = serializers.IntegerField()

    def validate_assigned_to_id(self, value):
        if not User.objects.filter(id=value, role__in=["support", "technical_support_admin"]).exists():
            raise serializers.ValidationError("Valid Support user ID required for assignment.")
        return value
    
class SupportStaffTicketStatsSerializer(serializers.Serializer):
    support_user_id = serializers.IntegerField(source="assigned_to_id")
    support_user_name = serializers.CharField(source="assigned_to__username")
    active_ticket_count = serializers.IntegerField()

class PublicCompanyDetailsSerializer(serializers.ModelSerializer):
    sso_providers = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    login_background_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'name', 
            'ticket_submission_url_slug', # The slug itself
            'logo_url', 
            'login_background_url', 
            'default_sso_provider_type',
            'sso_providers' # List of enabled provider types and their display info
        ]

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        # Return a default placeholder if no logo
        # return request.build_absolute_uri(settings.STATIC_URL + 'img/memoq_logo_placeholder.png') if request else None
        return None


    def get_login_background_url(self, obj):
        request = self.context.get('request')
        if obj.login_background and request:
            return request.build_absolute_uri(obj.login_background.url)
        # Return a default placeholder if no background
        # return request.build_absolute_uri(settings.STATIC_URL + 'img/localization_background.jpg') if request else None
        return None

    def get_sso_providers(self, obj):
        # Fetches enabled SSO providers for the company
        # This should return a list of objects/dicts, e.g., [{'provider_type': 'feishu', 'display_name': '飞书', 'app_id': '...'}, ...]
        # Only return necessary info for frontend to display buttons, not secrets.
        providers_data = []
        sso_provider_configs = CompanySSOProvider.objects.filter(company=obj, is_enabled=True)
        for config in sso_provider_configs:
            providers_data.append({
                "provider_type": config.provider_type,
                "display_name": config.get_provider_type_display(),
                # "app_id": config.app_id, # Frontend might need app_id for some client-side SDKs, but usually not for redirect flow
            })
        return providers_data