from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL


# =========================
#          الطالب
# =========================
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return getattr(self.user, "username", "student")


# =========================
#           الدورة
# =========================
class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    # نافذة زمنية اختيارية على مستوى الدورة
    start_date = models.DateField(null=True, blank=True)
    end_date   = models.DateField(null=True, blank=True)

    # مدة افتراضية (تُستخدم عند إنشاء Enrollment إن لم تُحدَّد تواريخ دقيقة)
    duration_days = models.PositiveIntegerField(default=30)

    # رابط Teams عام للدورة (يمكن تخصيصه لكل طالب عبر Enrollment.teams_link)
    teams_link = models.URLField(blank=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ("title",)

    @property
    def is_within_window(self) -> bool:
        """هل التاريخ الحالي داخل نافذة start_date/end_date إن وُجدت؟"""
        today = timezone.localdate()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True


# =========================
#      التسجيل في الدورة
# =========================
class Enrollment(models.Model):
    STATUS = (
        ("active", "نشط"),
        ("pending", "بانتظار"),
        ("expired", "منتهي"),
    )

    student   = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course    = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')

    status    = models.CharField(max_length=10, choices=STATUS, default="active")

    # وقت الانضمام + نافذة صلاحية الوصول (اختيارية)
    joined_at = models.DateTimeField(default=timezone.now)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at   = models.DateTimeField(null=True, blank=True)

    # تقدّم الطالب (٪)
    progress  = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # رابط Teams خاص بالتسجيل (لو تُرك فارغًا نرجع لرابط الدورة Course.teams_link)
    teams_link = models.URLField(blank=True)

    class Meta:
        unique_together = ('student', 'course')
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["course"]),
            models.Index(fields=["status"]),
        ]
        ordering = ("-joined_at",)

    def __str__(self) -> str:
        return f"{self.student} → {self.course} ({self.status})"

    @property
    def effective_teams_link(self) -> str:
        """يرجع رابط Teams الأكثر تحديدًا (التسجيل ثم الدورة)."""
        return self.teams_link or getattr(self.course, "teams_link", "")

    @property
    def is_within_window(self) -> bool:
        """تحقق زمن الوصول: إن وُجدت starts/ends نستخدمها؛ وإلا نتساهل."""
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    def activate_with_defaults(self) -> None:
        """
        تفعيل التسجيل مع تعيين نافذة زمنية افتراضية إذا لم تكن محددة:
        - starts_at = الآن (إن لم تكن موجودة)
        - ends_at   = starts_at + duration_days من الدورة
        """
        if not self.starts_at:
            self.starts_at = timezone.now()

        if not self.ends_at:
            days = getattr(self.course, "duration_days", 30) or 30
            self.ends_at = self.starts_at + timedelta(days=days)

        if not self.status:
            self.status = "active"


# =========================
#          الاختبارات
# =========================
class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title  = models.CharField(max_length=200)
    date   = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.title} - {self.course.title}"

    class Meta:
        ordering = ("-date",)


class ExamResult(models.Model):
    student   = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    exam      = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    score     = models.DecimalField(max_digits=5, decimal_places=2)
    graded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('student', 'exam')
        ordering = ("-graded_at",)
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["exam"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.exam} = {self.score}"


# =========================
#           الشهادات
# =========================
class Certificate(models.Model):
    student   = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    course    = models.ForeignKey(Course, on_delete=models.PROTECT)
    issued_at = models.DateField(default=timezone.now)
    file_url  = models.URLField(blank=True)

    class Meta:
        ordering = ("-issued_at",)

    def __str__(self) -> str:
        return f"شهادة {self.course} لـ {self.student}"


# =========================
#            الموارد
# =========================
class Resource(models.Model):
    title     = models.CharField(max_length=200)
    course    = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources', null=True, blank=True)
    file_url  = models.URLField()
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title
