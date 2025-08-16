from django.contrib import admin
from .models import TeacherProfile, Subject, Course, Lesson, Resource


# ========================
#   TeacherProfile
# ========================
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name")
    search_fields = ("user__username", "user__email", "full_name")
    ordering = ("id",)


# ========================
#   Subject
# ========================
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "stage")
    search_fields = ("name", "stage")
    list_filter = ("stage",)
    ordering = ("name",)


# ========================
#   Course
# ========================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "teacher",
        "subject",
        "is_active",
        "duration_days",
        "created_at",
    )
    list_filter = ("is_active", "subject__stage", "teacher")
    search_fields = (
        "title",
        "description",
        "subject__name",
        "teacher__full_name",
        "teacher__user__username",
        "teacher__user__email",
    )
    autocomplete_fields = ("teacher", "subject")
    list_editable = ("is_active",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("title", "description", "subject", "teacher")}),
        ("الحالة والمدة", {"fields": ("is_active", "duration_days")}),
        ("رابط Teams", {"fields": ("teams_link",)}),
        ("معلومات إضافية", {"fields": ("created_at",)}),
    )
    readonly_fields = ("created_at",)


# ========================
#   Lesson
# ========================
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "order", "title", "has_video", "has_slide")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    autocomplete_fields = ("course",)
    ordering = ("course", "order")

    def has_video(self, obj):
        return bool(obj.video_file or obj.recording_url)
    has_video.boolean = True
    has_video.short_description = "فيديو؟"

    def has_slide(self, obj):
        return bool(obj.slide_file or obj.slide_url)
    has_slide.boolean = True
    has_slide.short_description = "شرائح؟"


# ========================
#   Resource
# ========================
@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "title", "kind", "has_file", "has_link")
    list_filter = ("course", "kind")
    search_fields = ("title", "course__title")
    autocomplete_fields = ("course",)
    ordering = ("course", "title")

    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = "ملف؟"

    def has_link(self, obj):
        return bool(obj.external_link)
    has_link.boolean = True
    has_link.short_description = "رابط؟"
