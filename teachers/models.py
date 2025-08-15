# teachers/models.py
from django.db import models
from django.conf import settings

class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.full_name or self.user.get_full_name() or self.user.username


class Subject(models.Model):
    name = models.CharField(max_length=120)
    stage = models.CharField(max_length=120)

    class Meta:
        unique_together = ("name", "stage")
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self):
        return f"{self.name} - {self.stage}"


class Course(models.Model):
    teacher = models.ForeignKey('TeacherProfile', on_delete=models.CASCADE, related_name="courses")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="courses")
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    teams_link = models.URLField(blank=True)                 # اختياري
    duration_days = models.PositiveIntegerField(default=30)  # مدة الكورس
    is_active = models.BooleanField(default=True)            # حالة الكورس
    cover_image_url = models.URLField(blank=True)            # صورة غلاف (اختياري)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    order = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=150)
    content = models.TextField(blank=True)
    recording_url = models.URLField(blank=True)
    slide_url = models.URLField(blank=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Resource(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=150)
    file_url = models.URLField(blank=True)
    external_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ أضفناه ليلائم الـ admin

    def __str__(self):
        return self.title
