# orders/signals.py
from __future__ import annotations

from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from orders.models import Order
from students.models import Student, Enrollment
from teachers.models import Course


def _activate_enrollment(student: Student, course: Course) -> None:
    """
    تفعيل/إنشاء تسجيل نشط للطالب على الدورة مع نافذة زمنية افتراضية.
    العملية idempotent: إعادة الاستدعاء لن تكرّر التسجيل.
    """
    if not (student and course):
        return

    enr, _ = Enrollment.objects.get_or_create(student=student, course=course)

    # تعيين النوافذ الزمنية إن لزم
    if hasattr(enr, "activate_with_defaults"):
        enr.activate_with_defaults()
    else:
        if not enr.starts_at:
            enr.starts_at = timezone.now()
        if not enr.ends_at:
            days = getattr(course, "duration_days", 30) or 30
            enr.ends_at = enr.starts_at + timedelta(days=days)

    enr.status = "active"
    enr.save(update_fields=["status", "starts_at", "ends_at"])


@receiver(post_save, sender=Order)
def activate_on_paid(sender, instance: Order, created: bool, **kwargs):
    """
    عندما يصبح الطلب 'paid':
      - نحدد الطالب من order.user
      - نستخرج الدورة من المنتج المرتبط
      - نفعّل Enrollment
    """
    try:
        if instance.status != Order.STATUS_PAID:
            return

        user = getattr(instance, "user", None)
        if not user:
            return

        student, _ = Student.objects.get_or_create(user=user)

        # طلب منتج واحد
        product = getattr(instance, "product", None)
        if not product:
            return

        course = getattr(product, "course", None)
        if not course:
            return

        _activate_enrollment(student, course)

    except Exception:
        # يُفضَّل استخدام logging هنا
        # import logging; logging.getLogger(__name__).exception("activate_on_paid failed")
        pass
