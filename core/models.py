from django.db import models
from django.contrib.auth.models import AbstractUser

# ✅ خيارات الدور
ROLE_CHOICES = (
    ('student', 'طالب'),
    ('teacher', 'معلم'),
)

# ✅ نموذج المستخدم المخصص
class CustomUser(AbstractUser):
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name="الدور"
    )

    def is_student(self):
        return self.role == 'student'

    def is_teacher(self):
        return self.role == 'teacher'

    def __str__(self):
        return self.get_full_name() or self.username

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"


# ✅ نموذج رسائل "تواصل معنا"
class ContactMessage(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="الاسم"
    )
    email = models.EmailField(
        verbose_name="البريد الإلكتروني"
    )
    message = models.TextField(
        verbose_name="الرسالة"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإرسال"
    )

    def __str__(self):
        return f"{self.name} - {self.email}"

    class Meta:
        verbose_name = "رسالة تواصل"
        verbose_name_plural = "رسائل تواصل"
