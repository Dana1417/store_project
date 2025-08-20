# orders/apps.py
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"
    verbose_name = "إدارة الطلبات"

    def ready(self):
        """
        يتم استدعاء هذه الدالة عند تحميل التطبيق.
        - هنا نستورد signals لكي يتم تفعيلها مباشرة مع تشغيل Django.
        """
        try:
            import orders.signals  # noqa: F401
        except ImportError:
            # إذا لم يوجد ملف signals نتجاوز بدون خطأ
            pass
