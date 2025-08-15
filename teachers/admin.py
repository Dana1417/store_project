from django.contrib import admin
from .models import TeacherProfile, Subject, Course, Lesson, Resource


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name")
    search_fields = ("user__username", "user__email", "full_name")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "stage")
    search_fields = ("name", "stage")
    list_filter = ("stage",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "teacher", "subject", "is_active", "duration_days", "created_at")
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


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "order", "title")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    autocomplete_fields = ("course",)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "title")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    autocomplete_fields = ("course",)
