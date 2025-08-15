# teachers/urls.py
from django.urls import path
from . import views

app_name = "teachers"

urlpatterns = [
    path("dashboard/", views.teacher_dashboard, name="dashboard"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),

    # ✨ صفحات إنشاء داخل الموقع
    path("course/create/", views.create_course, name="create_course"),
    path("subject/create/", views.create_subject, name="create_subject"),

    # موجودة سابقًا (إن وُجدت في مشروعك)
    path("course/<int:course_id>/lesson/add/", views.add_lesson, name="add_lesson"),
    path("course/<int:course_id>/resource/add/", views.add_resource, name="add_resource"),
]
