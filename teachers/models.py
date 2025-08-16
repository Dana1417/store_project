# teachers/models.py
from __future__ import annotations

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.text import slugify
from django.utils import timezone


# =========================
#     دوال مسارات الرفع
# =========================
def lecture_upload_to(instance: "Lesson", filename: str) -> str:
    """
    حفظ ملفات المحاضرات ضمن مجلد يحمل كود المقرر.
    مثال: lectures/math101/2025-08-16_اسم_الملف.mp4
    """
    code = getattr(instance.course, "code", "") or slugify(instance.course.title)[:64]
    ts = timezone.now().strftime("%Y-%m-%d")
    return f"lectures/{code}/{ts}_{filename}"


def material_upload_to(instance: "Resource", filename: str) -> str:
    """
    حفظ ملفات المراجع/الكتب ضمن مجلد يحمل كود المقرر.
    مثال: materials/math101/2025-08-16_اسم_الملف.pdf
    """
    code = getattr(instance.course, "code", "") or slugify(instance.course.title)[:64]
    ts = timezone.now().strftime("%Y-%m-%d")
    return f"materials/{code}/{ts}_{filename}"


# =========================
#       نماذج المعلم
# =========================
class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True)

    def __str__(self) -> str:
        return self.full_name or self.user.get_full_name() or self.user.username


class Subject(models.Model):
    name = models.CharField(max_length=120)
    stage = models.CharField(max_length=120)

    class Meta:
        unique_together = ("name", "stage")
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        indexes = [
            models.Index(fields=["name", "stage"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.stage}"


class Course(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="courses")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="courses")
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    # تحسينات لإدارة المقرر
    code = models.SlugField(max_length=64, unique=True, blank=True, help_text="يُولَّد تلقائيًا إن تُرك فارغًا")
    teams_link = models.URLField(blank=True)
    duration_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    cover_image_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        # لتسهيل الاستدعاء من القوالب
        return f"/teachers/course/{self.pk}/"

    def clean(self):
        # التحقق من أن الروابط (إن وُجدت) تبدأ بـ https://
        def _ensure_https(value: str, field_name: str):
            if value and not str(value).startswith("https://"):
                raise ValidationError({field_name: "الرابط يجب أن يبدأ بـ https://"})
            # التحقق من صحة بنية الرابط عمومًا
            if value:
                URLValidator()(value)

        _ensure_https(self.teams_link, "teams_link")
        _ensure_https(self.cover_image_url, "cover_image_url")

        if self.duration_days < 1 or self.duration_days > 730:
            raise ValidationError({"duration_days": "المدة يجب أن تكون بين 1 و 730 يومًا."})

    def save(self, *args, **kwargs):
        # توليد كود مختصر إذا تُرك فارغًا
        if not self.code:
            base = slugify(self.title)[:50] or "course"
            suffix = str(int(timezone.now().timestamp()))[-6:]
            self.code = f"{base}-{suffix}"
        super().save(*args, **kwargs)

    @property
    def students_count(self) -> int:
        """
        عدّ طلاب هذا المقرر عبر علاقة Enrollment (في تطبيق الطلاب).
        ملاحظة: في الاستعلامات الثقيلة استخدم annotate باسم مختلف مثل students_total لتفادي
        تضارب الاسم مع خاصية @property.
        """
        rel = getattr(self, "enrollments", None)
        if rel is None:
            return 0
        try:
            return rel.count()
        except Exception:
            return 0


# =========================
#     الدروس/المحاضرات
# =========================
class Lesson(models.Model):
    """
    يمثّل محاضرة/درس داخل المقرر.
    يدعم إمّا:
      - رفع فيديو ملف (video_file) أو
      - وضع رابط خارجي للفيديو (recording_url)
    وكذلك شرائح العرض إمّا ملف أو رابط.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    order = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=150)
    content = models.TextField(blank=True)

    # فيديو المحاضرة: ملف أو رابط
    video_file = models.FileField(upload_to=lecture_upload_to, blank=True, null=True)
    recording_url = models.URLField(blank=True)

    # الشرائح: ملف أو رابط
    slide_file = models.FileField(upload_to=lecture_upload_to, blank=True, null=True)
    slide_url = models.URLField(blank=True)

    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["course", "order"], name="uniq_lesson_order_per_course"),
        ]
        indexes = [
            models.Index(fields=["course", "order"]),
        ]

    def __str__(self) -> str:
        return f"{self.course.title} — {self.title}"

    def clean(self):
        """
        قواعد:
          - للفيديو: يجب تحديد (video_file XOR recording_url)
          - للشرائح: اختيارية، وإن وُجدت فلتكن (slide_file XOR slide_url)
          - أي رابط يُستخدم يجب أن يكون https://
        """
        # فيديو
        if not self.video_file and not self.recording_url:
            raise ValidationError({"recording_url": "يجب رفع ملف فيديو أو إدخال رابط للمحاضرة."})
        if self.video_file and self.recording_url:
            raise ValidationError({"recording_url": "اختر طريقة واحدة للفيديو: ملف أو رابط."})
        if self.recording_url and not self.recording_url.startswith("https://"):
            raise ValidationError({"recording_url": "الرابط يجب أن يبدأ بـ https://"})

        # شرائح (اختيارية)
        if self.slide_file and self.slide_url:
            raise ValidationError({"slide_url": "اختر طريقة واحدة للشرائح: ملف أو رابط."})
        if self.slide_url and not self.slide_url.startswith("https://"):
            raise ValidationError({"slide_url": "الرابط يجب أن يبدأ بـ https://"})

        # تحقق من ترتيب موجب
        if self.order < 1:
            raise ValidationError({"order": "الترتيب يجب أن يكون 1 أو أكبر."})


# =========================
#     الموارد (كتب/مستندات)
# =========================
class Resource(models.Model):
    """
    مادة/كتاب/مرجع للمقرر.
    إمّا ملف مرفوع أو رابط خارجي.
    """
    TYPE_CHOICES = (
        ("book", "كتاب/مرجع"),
        ("sheet", "ملزمة/واجب"),
        ("slides", "شرائح عرض"),
        ("other", "أخرى"),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=150)

    # ملف أو رابط
    file = models.FileField(upload_to=material_upload_to, blank=True, null=True)
    external_link = models.URLField(blank=True)

    kind = models.CharField(max_length=20, choices=TYPE_CHOICES, default="other")
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["course", "kind"]),
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self):
        """
        - يجب اختيار طريقة واحدة: ملف أو رابط.
        - الروابط (إن وُجدت) يجب أن تبدأ بـ https://
        """
        if not self.file and not self.external_link:
            raise ValidationError({"external_link": "يجب إرفاق ملف أو إدخال رابط خارجي."})
        if self.file and self.external_link:
            raise ValidationError({"external_link": "اختر طريقة واحدة: ملف أو رابط."})
        if self.external_link and not self.external_link.startswith("https://"):
            raise ValidationError({"external_link": "الرابط يجب أن يبدأ بـ https://"})
