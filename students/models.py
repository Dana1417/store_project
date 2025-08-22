from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, CheckConstraint, UniqueConstraint
from django.utils import timezone
from django.utils.text import slugify

# =========================
#     متغير المستخدم
# =========================
User = settings.AUTH_USER_MODEL


# =========================
#      Validators/Utils
# =========================
def validate_https(url: str) -> None:
    """يضمن أن أي رابط مُدخل يستخدم HTTPS."""
    if not url:
        return
    scheme = urlparse(url).scheme.lower()
    if scheme not in ("https", ""):
        raise ValidationError("يجب أن يكون الرابط عبر HTTPS.")


def unique_slugify(instance, base: str, slug_field_name: str = "slug", max_length: int = 64) -> str:
    """يولّد slug فريدًا مع إضافة لاحقات إذا تكرر."""
    raw = (slugify(base or "", allow_unicode=True) or "course").strip("-")
    raw = raw[:max_length]
    ModelClass = instance.__class__
    candidate = raw
    i = 2
    while ModelClass.objects.filter(**{slug_field_name: candidate}).exclude(pk=instance.pk).exists():
        suffix = f"-{i}"
        candidate = (raw[: max_length - len(suffix)] + suffix).strip("-")
        i += 1
    return candidate or "course"


# =========================
#          الطالب
# =========================
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # ← أضفنا null/blank

    def __str__(self) -> str:
        return getattr(self.user, "username", f"طالب #{self.pk}")


# =========================
#           الدورة
# =========================
class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, db_index=True, allow_unicode=True, blank=True)

    is_active = models.BooleanField(default=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(default=30)

    teams_link = models.URLField(blank=True, validators=[validate_https])
    cover_image_url = models.URLField(blank=True, validators=[validate_https])

    class Meta:
        ordering = ("title",)
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def code(self) -> str:
        return self.slug

    @code.setter
    def code(self, value: str) -> None:
        self.slug = value

    @property
    def is_within_window(self) -> bool:
        today = timezone.localdate()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

    def get_absolute_url(self) -> str:
        from django.urls import reverse
        return reverse("students:course_detail", args=[self.code])

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = unique_slugify(self, self.title, slug_field_name="slug", max_length=64)
        super().save(*args, **kwargs)


# =========================
#      التسجيل في الدورة
# =========================
class Enrollment(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_PENDING = "pending"
    STATUS_EXPIRED = "expired"

    STATUS = (
        (STATUS_ACTIVE, "نشط"),
        (STATUS_PENDING, "بانتظار"),
        (STATUS_EXPIRED, "منتهي"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")

    status = models.CharField(max_length=10, choices=STATUS, default=STATUS_ACTIVE)

    joined_at = models.DateTimeField(default=timezone.now)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    teams_link = models.URLField(blank=True, validators=[validate_https])

    class Meta:
        constraints = [
            UniqueConstraint(fields=["student", "course"], name="uq_enrollment_student_course"),
            CheckConstraint(check=Q(progress__gte=0) & Q(progress__lte=100), name="ck_progress_0_100"),
        ]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["course"]),
            models.Index(fields=["status"]),
            models.Index(fields=["joined_at"]),
        ]
        ordering = ("-joined_at",)

    def __str__(self) -> str:
        return f"{self.student} ↔ {self.course} ({self.status})"

    @property
    def effective_teams_link(self) -> str:
        return self.teams_link or getattr(self.course, "teams_link", "")

    @property
    def is_within_window(self) -> bool:
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    def activate_with_defaults(self) -> None:
        if not self.starts_at:
            self.starts_at = timezone.now()
        if not self.ends_at:
            days = getattr(self.course, "duration_days", 30) or 30
            self.ends_at = self.starts_at + timedelta(days=days)
        if not self.status:
            self.status = self.STATUS_ACTIVE


# =========================
#          الاختبارات
# =========================
class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exams")
    title = models.CharField(max_length=200)
    date = models.DateTimeField()

    class Meta:
        ordering = ("-date",)
        indexes = [
            models.Index(fields=["course"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} - {self.course.title}"


class ExamResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="exam_results")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    score = models.DecimalField(max_digits=5, decimal_places=2)
    graded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["student", "exam"], name="uq_examresult_student_exam"),
        ]
        ordering = ("-graded_at",)
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["exam"]),
            models.Index(fields=["graded_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.exam} = {self.score}"


# =========================
#           الشهادات
# =========================
class Certificate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, null=True, blank=True)  # ← سمحنا بالفراغ مؤقتًا
    issued_at = models.DateField(default=timezone.localdate)
    file_url = models.URLField(blank=True, validators=[validate_https])

    class Meta:
        ordering = ("-issued_at",)
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["course"]),
            models.Index(fields=["issued_at"]),
        ]

    def __str__(self) -> str:
        return f"شهادة {self.course} لـ {self.student}"


# =========================
#            الموارد
# =========================
class Resource(models.Model):
    KIND_FILE = "file"
    KIND_LINK = "link"
    KIND_NOTE = "note"

    KINDS = [
        (KIND_FILE, "ملف"),
        (KIND_LINK, "رابط"),
        (KIND_NOTE, "ملاحظة"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="resources", null=True, blank=True)  # ← أضفنا null/blank
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=KINDS, default=KIND_FILE)

    file = models.FileField(upload_to="resources/files/", blank=True, null=True)
    external_link = models.URLField(blank=True, validators=[validate_https])
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # ← أضفنا null/blank

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["course"]),
            models.Index(fields=["kind"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.course})"
