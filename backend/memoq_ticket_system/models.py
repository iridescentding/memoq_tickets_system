from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
import uuid # For potential use with slugs or IDs

# --- User Model with Soft Delete ---
class UserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def get_queryset_with_deleted(self):
        return super().get_queryset()

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ROLE_SYSTEM_ADMIN) # Superuser is system admin

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CUSTOMER = "customer"
    ROLE_SUPPORT = "support"
    ROLE_TECHNICAL_SUPPORT_ADMIN = "technical_support_admin"
    ROLE_SYSTEM_ADMIN = "system_admin"
    ROLE_CHOICES = (
        (ROLE_CUSTOMER, "客户"),
        (ROLE_SUPPORT, "技术支持"),
        (ROLE_TECHNICAL_SUPPORT_ADMIN, "技术支持Admin"),
        (ROLE_SYSTEM_ADMIN, "系统管理员"),
    )

    company = models.ForeignKey(
        'Company', # Forward reference as string
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
        verbose_name="所属公司",
    )
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="电话")
    wechat_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="微信ID", db_index=True)
    feishu_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="飞书ID", db_index=True)
    enterprise_wechat_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="企业微信ID", db_index=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_CUSTOMER, verbose_name="角色")

    is_deleted = models.BooleanField(default=False, verbose_name="已软删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="软删除时间")

    objects = UserManager() # Default manager
    all_objects = BaseUserManager() # Manager to access all users including deleted

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False # Optionally deactivate on soft delete
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.save()

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

# --- Company and Related Models ---
class CustomerTypeTag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="名称")

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "客户类型标签"
        verbose_name_plural = "客户类型标签"

class Company(models.Model):
    # ... (Existing CHOICES for customer_type, professional_services, products, importance) ...
    CUSTOMER_TYPE_CHOICES = (
        ("formal_installation", "正式安装"), ("acceptance", "验收"), ("renewal", "续订"),
        ("contract", "合同"), ("trial", "试用"),
    )
    PROFESSIONAL_SERVICES_CHOICES = (("yes", "有"), ("no", "无"))
    PRODUCTS_CHOICES = (
        ("perpetual_tms", "永久TMS"), ("subscription_tms", "订阅TMS"), ("cloud", "cloud"),
        ("tp", "TP"), ("trial_tms", "试用TMS"), ("desktop_pm", "单机版PM"), ("desktop_pro", "单机版Pro"),
    )
    IMPORTANCE_CHOICES = (("vip", "VIP"), ("priority", "优先"), ("normal", "普通"))

    name = models.CharField(max_length=255, verbose_name="公司名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="公司代码")
    contact_person = models.CharField(max_length=255, verbose_name="联系人", blank=True, null=True)
    contact_email = models.EmailField(verbose_name="联系邮箱", blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="联系电话")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    customer_types = models.ManyToManyField(CustomerTypeTag, verbose_name="客户类型", blank=True)
    professional_services = models.CharField(max_length=20, choices=PROFESSIONAL_SERVICES_CHOICES, default="no", verbose_name="专业服务")
    logo = models.ImageField(upload_to="company_logos/", null=True, blank=True, verbose_name="公司Logo")
    products = models.CharField(max_length=50, choices=PRODUCTS_CHOICES, verbose_name="客户产品", blank=True, null=True)
    importance = models.CharField(max_length=20, choices=IMPORTANCE_CHOICES, default="normal", verbose_name="客户重要性")
    ticket_submission_url_slug = models.SlugField(max_length=100, unique=True, null=True, blank=True, verbose_name="工单提交URL标识")
    login_background = models.ImageField(upload_to="company_backgrounds/", null=True, blank=True, verbose_name="登录页背景图")
    email_config = models.JSONField(default=dict, blank=True, null=True, verbose_name="邮件系统配置 (SMTP)")
    default_sso_provider_type = models.CharField(
        max_length=50, blank=True, null=True,
        choices=[('feishu', '飞书'), ('enterprise_wechat', '企业微信'), ('wechat', '微信')], # Add more as needed
        verbose_name="默认SSO提供商类型"
    )


    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "公司"
        verbose_name_plural = "公司"

class CompanySSOProvider(models.Model):
    PROVIDER_CHOICES = [
        ('feishu', '飞书'),
        ('enterprise_wechat', '企业微信'),
        ('wechat', '微信'), # For regular WeChat OAuth if supported
        # Add other providers as needed
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sso_providers", verbose_name="公司")
    provider_type = models.CharField(max_length=50, choices=PROVIDER_CHOICES, verbose_name="提供商类型")
    is_enabled = models.BooleanField(default=False, verbose_name="是否启用")
    app_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="App ID / Corp ID")
    app_secret = models.CharField(max_length=255, blank=True, null=True, verbose_name="App Secret / Corp Secret")
    agent_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Agent ID (企业微信/部分飞书应用)") # If needed
    webhook_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="消息通知Webhook URL")
    # Add other provider-specific fields as JSON or individual fields
    additional_config = models.JSONField(default=dict, blank=True, null=True, verbose_name="其他配置")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "公司SSO提供商配置"
        verbose_name_plural = "公司SSO提供商配置"
        unique_together = ('company', 'provider_type') # Each company can have one config per provider type

    def __str__(self):
        return f"{self.company.name} - {self.get_provider_type_display()}"


class CompanyConfig(models.Model):
    # ... (Existing model content, no major changes here unless SLA is tied to SSO provider details) ...
    SLA_LEVEL_CHOICES = (("basic", "基础"), ("standard", "标准"), ("premium", "高级"))
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="config", verbose_name="公司")
    sla_level = models.CharField(max_length=20, choices=SLA_LEVEL_CHOICES, default="standard", verbose_name="SLA级别")
    priority_level = models.IntegerField(default=3, verbose_name="优先级")
    idle_timeout_minutes = models.IntegerField(default=1440, verbose_name="闲置超时(分钟)")
    sla_response_minutes = models.IntegerField(default=240, verbose_name="SLA响应(分钟)") # IR
    sla_resolution_minutes = models.IntegerField(default=2880, verbose_name="SLA解决(分钟)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "公司配置 (SLA等)"
        verbose_name_plural = "公司配置 (SLA等)"

# --- Ticket Related Models ---
class TicketType(MPTTModel):
    # ... (Existing model content, ensure created_by uses SET_NULL and allows null) ...
    name = models.CharField(max_length=100, verbose_name="类型名称")
    description = models.TextField(blank=True, null=True, verbose_name="类型描述")
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="父类型")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="created_ticket_types", null=True, blank=True, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="是否激活")

    def __str__(self): return self.name
    class MPTTMeta: order_insertion_by = ['name']
    class Meta:
        verbose_name = "工单类型"
        verbose_name_plural = "工单类型"

class TicketLabel(models.Model):
    # ... (Existing model content) ...
    name = models.CharField(max_length=50, unique=True, verbose_name="标签名称")
    color = models.CharField(max_length=20, default="#3f51b5", verbose_name="标签颜色")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="标签描述")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.name
    class Meta:
        verbose_name = "工单标签"
        verbose_name_plural = "工单标签"

class Ticket(models.Model):
    # ... (Existing CHOICES) ...
    STATUS_CHOICES = (
        ("new_issue", "新问题"), ("pending_assignment", "待分配"), ("in_progress", "处理中"),
        ("waiting_for_customer", "等待客户回复"), ("resolved", "已解决"), ("closed", "已关闭"),
        ("customer_follow_up", "追问"), ("paused", "暂停"),
    )
    CONTACT_METHOD_CHOICES = (
        ("email", "邮箱"), ("wechat", "微信"), ("enterprise_wechat", "企业微信"),
        ("feishu", "飞书"), ("phone", "电话"),
    )
    CLOSING_REASON_CHOICES = (
        ("customer_completed", "客户已完成"), ("on_hold", "暂时挂起"), ("bug_report", "bug"),
        ("feature_request", "新需求"), ("other", "其他"),
    )
    URGENCY_CHOICES = ((1, "紧急"), (2, "高"), (3, "中"), (4, "低"))

    title = models.CharField(max_length=255, verbose_name="标题")
    description = models.TextField(verbose_name="描述")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="tickets", verbose_name="所属公司")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="created_tickets", null=True, blank=True, verbose_name="创建人")
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="submitted_tickets", verbose_name="提交人", null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="assigned_tickets", null=True, blank=True, verbose_name="负责人")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="new_issue", verbose_name="状态", db_index=True)
    priority = models.IntegerField(default=3, verbose_name="优先级 (系统)")
    urgency = models.IntegerField(choices=URGENCY_CHOICES, default=3, verbose_name="紧急度 (用户/支持设定)")
    category = models.CharField(max_length=100, verbose_name="类别", blank=True, null=True) # Potentially TicketType based
    subcategory = models.CharField(max_length=100, blank=True, null=True, verbose_name="子类别") # Potentially TicketType based
    contact_method = models.CharField(max_length=30, choices=CONTACT_METHOD_CHOICES, default="email", verbose_name="联系方式")
    contact_info = models.CharField(max_length=255, verbose_name="联系信息", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(default=timezone.now, verbose_name="最后活动时间", db_index=True)
    first_replied_at = models.DateTimeField(null=True, blank=True, verbose_name="首次回复时间", db_index=True) # For IR SLA
    last_customer_reply_at = models.DateTimeField(null=True, blank=True, verbose_name="客户最后回复时间")
    last_support_reply_at = models.DateTimeField(null=True, blank=True, verbose_name="支持最后回复时间")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="解决时间")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="关闭时间")
    paused_at = models.DateTimeField(null=True, blank=True, verbose_name="暂停时间")
    pause_reason = models.TextField(blank=True, null=True, verbose_name="暂停原因")
    closing_reason_type = models.CharField(max_length=50, choices=CLOSING_REASON_CHOICES, null=True, blank=True, verbose_name="关闭原因类型")
    closing_reason_detail = models.TextField(max_length=100, null=True, blank=True, verbose_name="关闭原因详情")
    ticket_type = models.ForeignKey(TicketType, on_delete=models.SET_NULL, related_name="tickets", null=True, blank=True, verbose_name="工单类型", db_index=True)
    labels = models.ManyToManyField(TicketLabel, related_name="tickets", blank=True, verbose_name="工单标签")
    followers = models.ManyToManyField(User, related_name="following_tickets", blank=True, verbose_name="关注人")
    ticket_url_slug = models.SlugField(max_length=100, unique=True, null=True, blank=True, verbose_name="工单URL标识", db_index=True)

    # SLA Deadlines
    sla_ir_deadline = models.DateTimeField(null=True, blank=True, verbose_name="SLA首次响应截止时间")
    sla_resolution_deadline = models.DateTimeField(null=True, blank=True, verbose_name="SLA解决截止时间")
    # is_ir_sla_missed = models.BooleanField(default=False, verbose_name="首次响应SLA是否已错过")
    # is_resolution_sla_missed = models.BooleanField(default=False, verbose_name="解决SLA是否已错过")
    # is_idle = models.BooleanField(default=False, verbose_name="是否闲置")

    def save(self, *args, **kwargs):
        if not self.submitted_by_id and self.created_by_id:
            self.submitted_by = self.created_by
        # SLA deadline calculation logic could go here or in a signal
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.calculate_sla_deadlines() # Calculate on creation
            self.save(update_fields=['sla_ir_deadline', 'sla_resolution_deadline'])


    def calculate_sla_deadlines(self):
        if self.company and hasattr(self.company, 'config'):
            config = self.company.config
            if config.sla_response_minutes:
                self.sla_ir_deadline = self.created_at + timezone.timedelta(minutes=config.sla_response_minutes)
            if config.sla_resolution_minutes:
                self.sla_resolution_deadline = self.created_at + timezone.timedelta(minutes=config.sla_resolution_minutes)
        # Consider business hours if applicable

    def __str__(self): return f"{self.id} - {self.title}"
    class Meta:
        verbose_name = "工单"
        verbose_name_plural = "工单"
        # Removed old indexes, new ones will be generated by makemigrations
        # Or add them back carefully if they are still exactly what you need.
        # For now, relying on db_index=True on individual fields.

class TicketReply(models.Model):
    # ... (Existing model content, ensure user uses SET_NULL and allows null) ...
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="replies", verbose_name="工单")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="ticket_replies", null=True, blank=True, verbose_name="回复人")
    content = models.TextField(verbose_name="内容")
    is_internal = models.BooleanField(default=False, verbose_name="是否内部备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email_sent = models.BooleanField(default=False, verbose_name="邮件已发送")
    email_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="邮件发送时间")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update ticket's last_activity_at and potentially customer/support reply times
        ticket = self.ticket
        ticket.last_activity_at = self.created_at
        if self.user:
            if self.user.role == User.ROLE_CUSTOMER:
                ticket.last_customer_reply_at = self.created_at
                if ticket.status == Ticket.STATUS_CHOICES[3][0]: # waiting_for_customer
                    ticket.status = Ticket.STATUS_CHOICES[6][0] # customer_follow_up (追问)
            else: # Support or Admin
                ticket.last_support_reply_at = self.created_at
                if not ticket.first_replied_at: # Check if this is the first support reply
                    ticket.first_replied_at = self.created_at
        ticket.save()


    class Meta:
        verbose_name = "工单回复"
        verbose_name_plural = "工单回复"
        ordering = ["created_at"]


class Attachment(models.Model):
    # ... (Existing model content, ensure uploaded_by uses SET_NULL and allows null) ...
    file_name = models.CharField(max_length=255, verbose_name="文件名")
    file = models.FileField(upload_to="attachments/%Y/%m/%d/", verbose_name="文件")
    file_size = models.IntegerField(verbose_name="文件大小(字节)")
    file_type = models.CharField(max_length=100, verbose_name="文件类型")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments", null=True, blank=True, verbose_name="关联工单")
    reply = models.ForeignKey(TicketReply, on_delete=models.CASCADE, related_name="attachments", null=True, blank=True, verbose_name="关联回复")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="uploaded_attachments", null=True, blank=True, verbose_name="上传人")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.file_name
    class Meta:
        verbose_name = "附件"
        verbose_name_plural = "附件"


class TicketStatusHistory(models.Model):
    # ... (Existing model content, ensure changed_by uses SET_NULL and allows null) ...
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="status_history", verbose_name="工单")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="status_changes", null=True, blank=True, verbose_name="变更人")
    old_status = models.CharField(max_length=30, choices=Ticket.STATUS_CHOICES, verbose_name="原状态")
    new_status = models.CharField(max_length=30, choices=Ticket.STATUS_CHOICES, verbose_name="新状态")
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True, verbose_name="变更原因")

    class Meta:
        verbose_name = "工单状态历史"
        verbose_name_plural = "工单状态历史"
        ordering = ["created_at"]

class TicketTransferHistory(models.Model):
    # ... (Existing model content, ensure user fields use SET_NULL and allow null) ...
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="transfer_history", verbose_name="工单")
    transferred_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="transferred_tickets_initiated", null=True, blank=True, verbose_name="转移发起人")
    transferred_from = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="transfers_from_user", null=True, blank=True, verbose_name="原负责人")
    transferred_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="transfers_to_user", null=True, blank=True, verbose_name="新负责人")
    reason = models.TextField(verbose_name="转移原因")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "工单转移历史"
        verbose_name_plural = "工单转移历史"
        ordering = ["created_at"]

class TicketSatisfactionRating(models.Model):
    RATING_CHOICES = [
        (1, '很不满意'), (2, '不满意'), (3, '一般'), (4, '满意'), (5, '非常满意')
    ]
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="satisfaction_rating", verbose_name="工单")
    rated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="评价人 (客户)")
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name="评分")
    comment = models.TextField(blank=True, null=True, verbose_name="评论")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评价时间")

    class Meta:
        verbose_name = "工单满意度评价"
        verbose_name_plural = "工单满意度评价"
        ordering = ["-created_at"]

    def __str__(self):
        return f"工单 #{self.ticket.id} - 评分: {self.get_rating_display()}"

# --- Notification System Models ---
class NotificationConfig(models.Model): # User-specific notification preferences
    # ... (Existing model content) ...
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notification_config", verbose_name="用户")
    email_enabled = models.BooleanField(default=True, verbose_name="启用邮件通知")
    wechat_enabled = models.BooleanField(default=False, verbose_name="启用微信通知") # User preference
    enterprise_wechat_enabled = models.BooleanField(default=False, verbose_name="启用企业微信通知") # User preference
    feishu_enabled = models.BooleanField(default=False, verbose_name="启用飞书通知") # User preference
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "用户通知配置"
        verbose_name_plural = "用户通知配置"

class NotificationTemplate(models.Model):
    EVENT_TYPE_CHOICES = (
        ("ticket_created", "工单创建"),
        ("ticket_status_changed", "工单状态变更"),
        ("ticket_replied_by_support", "技术支持回复"),
        ("ticket_replied_by_customer", "客户回复"),
        ("ticket_assigned", "工单分配"),
        ("ticket_transferred", "工单转移"),
        ("ticket_paused", "工单暂停"),
        ("ticket_sla_ir_warning", "SLA首次响应预警"),
        ("ticket_sla_ir_missed", "SLA首次响应错过"),
        ("ticket_sla_resolution_warning", "SLA解决预警"),
        ("ticket_sla_resolution_missed", "SLA解决错过"),
        ("ticket_idle_warning", "工单闲置预警"),
    )
    CHANNEL_CHOICES = (
        ('email', '邮件'),
        ('feishu', '飞书'),
        ('enterprise_wechat', '企业微信'),
        # Add more channels as needed
    )
    name = models.CharField(max_length=100, unique=True, verbose_name="模板名称")
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, verbose_name="事件类型")
    channel = models.CharField(max_length=30, choices=CHANNEL_CHOICES, verbose_name="通知渠道")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    subject_template = models.CharField(max_length=255, verbose_name="主题/标题模板 (支持变量)")
    body_template = models.TextField(verbose_name="内容模板 (支持变量，邮件可为HTML，Webhook为Markdown/JSON)")
    # For company-specific templates, add a ForeignKey to Company (optional=True for global templates)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name="notification_templates", verbose_name="所属公司 (可选,全局则为空)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "通知模板"
        verbose_name_plural = "通知模板"
        # unique_together = [("company", "event_type", "channel")] # If company is not null

    def __str__(self):
        return f"{self.name} ({self.get_event_type_display()} - {self.get_channel_display()})"


class NotificationLog(models.Model):
    # ... (Existing model content, ensure user field uses SET_NULL and allows null) ...
    NOTIFICATION_TYPE_CHOICES = (
        ("email", "邮箱"), ("wechat", "微信"), ("enterprise_wechat", "企业微信"),
        ("feishu", "飞书"), ("webhook", "Webhook通用"),
    )
    STATUS_CHOICES = (
        ("pending", "待发送"), ("sent", "已发送"), ("failed", "发送失败"), ("retry_failed", "重试失败"),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="notifications_triggered_log", null=True, blank=True, verbose_name="触发用户")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="notification_logs", null=True, blank=True, verbose_name="公司")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="notification_logs", verbose_name="工单")
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES, verbose_name="通知类型")
    recipient_info = models.CharField(max_length=255, blank=True, null=True, verbose_name="接收者信息(如邮箱/Webhook URL)")
    content_summary = models.TextField(verbose_name="内容摘要/主题") # Changed from 'content'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="状态")
    retry_attempts = models.IntegerField(default=0, verbose_name="重试次数")
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="发送时间")
    response_info = models.TextField(blank=True, null=True, verbose_name="发送响应信息")


    class Meta:
        verbose_name = "通知记录"
        verbose_name_plural = "通知记录"
# Removed WebhookTemplate and EmailTemplate as they are superseded by NotificationTemplate
# If you still need the old WebhookTemplate for other purposes, you can keep it, but
# for user notifications, NotificationTemplate is more generic.
# For simplicity of this exercise, I'm assuming NotificationTemplate replaces them for these user-facing notifications.
# If WebhookTemplate was for system-to-system generic webhooks, then it's fine to keep.
# Let's assume for now we consolidate into NotificationTemplate.
 