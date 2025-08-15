from django.contrib import admin
from .models import Student, Enrollment


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    raw_id_fields = ("course",)
    fields = ("course", "status", "joined_at", "starts_at", "ends_at", "teams_link")
    show_change_link = True


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__username", "user__email")
    ordering = ("id",)
    raw_id_fields = ("user",)
    inlines = (EnrollmentInline,)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "course", "status", "joined_at")
    list_filter = ("status", "course")
    search_fields = (
        "student__user__username",
        "student__user__email",
        "course__title",
    )
    ordering = ("-joined_at", "id")
    date_hierarchy = "joined_at"
    raw_id_fields = ("student", "course")
