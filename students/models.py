from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, CheckConstraint, UniqueConstraint
from django.utils import timezone
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


# =========================
#      Validators/Utils
# =========================
def validate_https(url: str) -> None:
    """
    يضمن أن أي رابط مُدخل يستخدم HTTPS.
    """
    if not url:
        return
    scheme = urlparse(url).scheme.lower()
    if scheme not in ("https", ""):  # نسمح بالفراغ كي لا نفشل عند الحقول الاختيارية قبل الحفظ
        raise ValidationError("يجب أن يكون الرابط عبر HTTPS.")


def unique_slugify(instance, base: str, slug_field_name: str = "slug", max_length: int = 64) -> str:
    """
    يولّد slug فريدًا من base مع إضافة لاحقات -2, -3... عند التكرار.
    """
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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return getattr(self.user, "username", "student")


# =========================
#           الدورة
# =========================
class Course(models.Model):
    title = models.CharField(max_length=200)
    # نبقي slug كمصدر الحقيقة، ونوفّر alias اسمه code لاستخدامه في القوالب/الروابط
    slug = models.SlugField(unique=True, db_index=True, allow_unicode=True, blank=True)

    is_active = models.BooleanField(default=True)

    # نافذة زمنية اختيارية على مستوى الدورة
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # مدة افتراضية تُستخدم عند إنشاء Enrollment إن لم تُحدّد تواريخ دقيقة
    duration_days = models.PositiveIntegerField(default=30)

    # رابط Teams عام للدورة (HTTPS)
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

    # ---- code alias (للتوافق مع القوالب ومناطق أخرى) ----
    @property
    def code(self) -> str:
        return self.slug

    @code.setter
    def code(self, value: str) -> None:
        self.slug = value

    # ---- منافع ----
    @property
    def is_within_window(self) -> bool:
        """هل التاريخ الحالي داخل نافذة start_date/end_date إن وُجدت؟"""
        today = timezone.localdate()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

    def get_absolute_url(self) -> str:
        """
        مفيد للقوالب: course.get_absolute_url
        يتوقع أن لديك url باسم students:course_detail <slug:code>
        """
        from django.urls import reverse
        return reverse("students:course_detail", args=[self.code])

    # ---- الحفظ مع توليد slug عند الحاجة ----
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

    # وقت الانضمام + نافذة صلاحية الوصول (اختيارية)
    joined_at = models.DateTimeField(default=timezone.now)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    # تقدّم الطالب (٪ من 0 إلى 100)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # رابط Teams خاص بالتسجيل (HTTPS). إن تُرك فارغًا نرجع لرابط الدورة Course.teams_link
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
        return f"{self.student} → {self.course} ({self.status})"

    @property
    def effective_teams_link(self) -> str:
        """يرجع رابط Teams الأكثر تحديدًا (التسجيل ثم الدورة)."""
        return self.teams_link or getattr(self.course, "teams_link", "")

    @property
    def is_within_window(self) -> bool:
        """
        تحقق زمن الوصول: إن وُجدت starts/ends نستخدمها؛
        وإلا نتساهل (نعتبره ضمن النافذة) حتى لا نمنع الدخول دون إعدادات.
        """
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    def activate_with_defaults(self) -> None:
        """
        تفعيل التسجيل مع تعيين نافذة زمنية افتراضية إذا لم تكن محددة:
        - starts_at = الآن (إن لم تكن)
        - ends_at   = starts_at + duration_days من الدورة
        """
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
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    issued_at = models.DateField(default=timezone.now)
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
    title = models.CharField(max_length=200)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="resources", null=True, blank=True
    )
    file_url = models.URLField(validators=[validate_https])
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ("title",)
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["is_public"]),
        ]

    def __str__(self) -> str:
        return self.title
