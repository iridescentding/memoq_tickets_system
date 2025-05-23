from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from mptt.admin import DraggableMPTTAdmin # For TicketType

from memoq_ticket_system.models import (
    User, Company, Ticket, TicketReply, CompanyConfig, Attachment,
    CustomerTypeTag, NotificationConfig, NotificationLog,
    TicketStatusHistory, TicketType, TicketLabel, TicketTransferHistory,
    CompanySSOProvider, NotificationTemplate, TicketSatisfactionRating # New models
)

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("自定义字段", {"fields": ("role", "company", "phone", "wechat_id", "feishu_id", "enterprise_wechat_id", "is_deleted", "deleted_at")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("自定义字段", {"fields": ("role", "company", "phone", "wechat_id", "feishu_id", "enterprise_wechat_id", "email", "first_name", "last_name")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "role", "company", "is_staff", "is_active", "is_deleted")
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "is_deleted", "groups", "company")
    search_fields = ("username", "first_name", "last_name", "email", "company__name")
    ordering = ("username",)
    actions = ['soft_delete_selected', 'restore_selected']

    def get_queryset(self, request):
        # Show all users (including soft-deleted) in admin
        return User.all_objects.all()

    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
    soft_delete_selected.short_description = "软删除选中的用户"

    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
    restore_selected.short_description = "恢复选中的用户"


class CompanySSOProviderInline(admin.TabularInline): # Or admin.StackedInline
    model = CompanySSOProvider
    extra = 1 # Number of empty forms to display

class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "contact_person", "contact_email", "importance", "default_sso_provider_type", "created_at")
    search_fields = ("name", "code", "contact_person", "contact_email")
    list_filter = ("importance", "created_at", "products", "professional_services", "default_sso_provider_type")
    ordering = ("-importance", "name")
    inlines = [CompanySSOProviderInline]


class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "company", "created_by", "assigned_to", "status",
        "priority", "urgency", "ticket_type", "created_at", "last_activity_at",
        "sla_ir_deadline", "sla_resolution_deadline"
    )
    list_filter = ("status", "priority", "urgency", "company", "ticket_type", "created_at", "assigned_to")
    search_fields = ("id", "title", "description", "company__name", "created_by__username", "assigned_to__username")
    ordering = ("-last_activity_at",)
    raw_id_fields = ("company", "created_by", "submitted_by", "assigned_to", "ticket_type")
    readonly_fields = ("sla_ir_deadline", "sla_resolution_deadline", "last_customer_reply_at", "last_support_reply_at")


class TicketSatisfactionRatingAdmin(admin.ModelAdmin):
    list_display = ("ticket", "rated_by", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("ticket__title", "rated_by__username", "comment")
    raw_id_fields = ("ticket", "rated_by")

class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "event_type", "channel", "is_active", "updated_at")
    list_filter = ("company", "event_type", "channel", "is_active")
    search_fields = ("name", "subject_template", "body_template", "company__name")
    ordering = ("company", "name")


admin.site.register(User, UserAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketReply, admin.ModelAdmin) # Basic registration for now
admin.site.register(Attachment, admin.ModelAdmin) # Basic
admin.site.register(CompanyConfig, admin.ModelAdmin) # Basic
admin.site.register(CustomerTypeTag, admin.ModelAdmin) # Basic
admin.site.register(NotificationConfig, admin.ModelAdmin) # Basic
admin.site.register(NotificationLog, admin.ModelAdmin) # Basic
admin.site.register(TicketStatusHistory, admin.ModelAdmin) # Basic
admin.site.register(TicketTransferHistory, admin.ModelAdmin) # Basic
admin.site.register(TicketType, DraggableMPTTAdmin) # Using MPTT admin
admin.site.register(TicketLabel, admin.ModelAdmin) # Basic
admin.site.register(CompanySSOProvider, admin.ModelAdmin) # Basic, or customize
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)
admin.site.register(TicketSatisfactionRating, TicketSatisfactionRatingAdmin)