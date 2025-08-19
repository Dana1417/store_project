# orders/apps.py
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"

    def ready(self):
        """
        يتم استدعاء هذه الدالة عند تحميل التطبيق.
        هنا نقوم بتحميل ملف signals لربط الإشعارات (signals)
        مثل تفعيل تسجيل الطالب في الدورة بعد الدفع.
        """
        import orders.signals  # noqa: F401
