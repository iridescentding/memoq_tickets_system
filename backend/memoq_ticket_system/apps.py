from django.apps import AppConfig


class MemoqTicketSystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "memoq_ticket_system"

    def ready(self):
        # 导入信号处理器
        import memoq_ticket_system.signals
