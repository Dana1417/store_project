# students/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Student

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_student_profile(sender, instance, created, **kwargs):
    """
    ينشئ سجل Student تلقائياً للمستخدمين بدور 'student'.
    - عند الإنشاء لأول مرة.
    - وأيضاً إذا تغير الدور لاحقاً إلى 'student' ولا يوجد سجل Student.
    يستعمل get_or_create لتجنب التكرار.
    """
    is_student = getattr(instance, "role", None) == "student"

    if created and is_student:
        Student.objects.get_or_create(user=instance)
        return

    # في حفظات لاحقة: لو صار الدور طالب ولا يوجد سجل
    if not created and is_student:
        Student.objects.get_or_create(user=instance)
