from __future__ import annotations

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, FileExtensionValidator
from django.utils.text import slugify
from django.utils import timezone

ALLOWED_VIDEO_EXTS = ["mp4", "mov", "mkv", "webm"]
ALLOWED_SLIDE_EXTS = ["pdf", "ppt", "pptx", "pptm"]
ALLOWED_DOC_EXTS = ["pdf", "doc", "docx", "ppt", "pptx", "xlsx", "zip"]

MAX_VIDEO_MB = 500
MAX_FILE_MB = 100


def _validate_https(url: str, field_name: str):
    if url:
        if not str(url).startswith("https://"):
            raise ValidationError({field_name: "الرابط يجب أن يبدأ بـ https://"})
        URLValidator()(url)


def _validate_filesize(f, max_mb: int, field_name: str):
    if f and hasattr(f, "size") and f.size and f.size > max_mb * 1024 * 1024:
        raise ValidationError({field_name: f"حجم الملف يتجاوز {max_mb}MB"})


def lecture_upload_to(instance: "Lesson", filename: str) -> str:
    code = getattr(instance.course, "code", "") or slugify(instance.course.title)[:64]
    ts = timezone.now().strftime("%Y-%m-%d")
    return f"lectures/{code}/{ts}_{filename}"


def material_upload_to(instance: "Resource", filename: str) -> str:
    code = getattr(instance.course, "code", "") or slugify(instance.course.title)[:64]
    ts = timezone.now().strftime("%Y-%m-%d")
    return f"materials/{code}/{ts}_{filename}"


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
        indexes = [models.Index(fields=["name", "stage"])]

    def __str__(self) -> str:
        return f"{self.name} - {self.stage}"


class CourseQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Course(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="courses")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="courses")
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    code = models.SlugField(max_length=64, unique=True, blank=True,
                            help_text="يُولَّد تلقائيًا إن تُرك فارغًا.")
    teams_link = models.URLField("رابط Microsoft Teams", blank=True)
    duration_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    cover_image_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = CourseQuerySet.as_manager()

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["code"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return f"/teachers/course/{self.pk}/"

    @property
    def has_teams(self) -> bool:
        return bool(self.teams_link)

    @property
    def students_count(self) -> int:
        rel = getattr(self, "enrollments", None)
        try:
            return rel.count() if rel is not None else 0
        except Exception:
            return 0

    def clean(self):
        _validate_https(self.teams_link, "teams_link")
        _validate_https(self.cover_image_url, "cover_image_url")
        if not (1 <= self.duration_days <= 730):
            raise ValidationError({"duration_days": "المدة يجب أن تكون بين 1 و 730 يومًا."})

    def save(self, *args, **kwargs):
        if not self.code:
            base = slugify(self.title)[:50] or "course"
            suffix = str(int(timezone.now().timestamp()))[-6:]
            self.code = f"{base}-{suffix}"
        super().save(*args, **kwargs)


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    order = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=150)
    content = models.TextField(blank=True)

    video_file = models.FileField(
        upload_to=lecture_upload_to, blank=True, null=True,
        validators=[FileExtensionValidator(ALLOWED_VIDEO_EXTS)],
    )
    recording_url = models.URLField(blank=True)

    slide_file = models.FileField(
        upload_to=lecture_upload_to, blank=True, null=True,
        validators=[FileExtensionValidator(ALLOWED_SLIDE_EXTS)],
    )
    slide_url = models.URLField(blank=True)

    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["course", "order"],
                                    name="uniq_lesson_order_per_course"),
        ]
        indexes = [models.Index(fields=["course", "order"])]

    def __str__(self) -> str:
        return f"{self.course.title} — {self.title}"

    def clean(self):
        if not self.video_file and not self.recording_url:
            raise ValidationError({"recording_url": "يجب رفع ملف فيديو أو إدخال رابط للمحاضرة."})
        if self.video_file and self.recording_url:
            raise ValidationError({"recording_url": "اختر طريقة واحدة للفيديو: ملف أو رابط."})
        if self.recording_url:
            _validate_https(self.recording_url, "recording_url")
        _validate_filesize(self.video_file, MAX_VIDEO_MB, "video_file")

        if self.slide_file and self.slide_url:
            raise ValidationError({"slide_url": "اختر طريقة واحدة للشرائح: ملف أو رابط."})
        if self.slide_url:
            _validate_https(self.slide_url, "slide_url")
        _validate_filesize(self.slide_file, MAX_FILE_MB, "slide_file")

        if self.order < 1:
            raise ValidationError({"order": "الترتيب يجب أن يكون 1 أو أكبر."})


class Resource(models.Model):
    TYPE_CHOICES = (
        ("book", "كتاب/مرجع"),
        ("sheet", "ملزمة/واجب"),
        ("slides", "شرائح عرض"),
        ("other", "أخرى"),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=150)

    file = models.FileField(
        upload_to=material_upload_to, blank=True, null=True,
        validators=[FileExtensionValidator(ALLOWED_DOC_EXTS + ALLOWED_SLIDE_EXTS)],
    )
    external_link = models.URLField(blank=True)

    kind = models.CharField(max_length=20, choices=TYPE_CHOICES, default="other")
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["course", "kind", "created_at"])]

    def __str__(self) -> str:
        return self.title

    def clean(self):
        if not self.file and not self.external_link:
            raise ValidationError({"external_link": "يجب إرفاق ملف أو إدخال رابط خارجي."})
        if self.file and self.external_link:
            raise ValidationError({"external_link": "اختر طريقة واحدة: ملف أو رابط."})
        if self.external_link:
            _validate_https(self.external_link, "external_link")
        _validate_filesize(self.file, MAX_FILE_MB, "file")
