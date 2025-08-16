# teachers/urls.py
from django.urls import path
from . import views

app_name = "teachers"

urlpatterns = [
    # لوحة المعلّم
    path("dashboard/", views.teacher_dashboard, name="dashboard"),

    # تفاصيل مقرر معيّن (طلاب + محاضرات + موارد)
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),

    # إنشاء محاضرة/مرجع داخل مقرر (للمعلّم على مقرراته)
    path("course/<int:course_id>/lesson/add/", views.add_lesson, name="add_lesson"),
    path("course/<int:course_id>/resource/add/", views.add_resource, name="add_resource"),

    # إنشاء مادة وكورس (مخصّص للمشرف فقط داخل الفيوز)
    path("subject/new/", views.create_subject, name="create_subject"),
    path("course/new/", views.create_course, name="create_course"),
]
