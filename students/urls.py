# students/urls.py
from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("courses/", views.my_courses, name="my_courses"),
    path("exams/", views.my_exams, name="my_exams"),
    path("certs/", views.my_certs, name="my_certs"),
    path("resources/", views.my_resources, name="my_resources"),
    path("profile/", views.my_profile, name="my_profile"),

    # ✅ روابط مباشرة بالـ pk
    path("course/id/<int:pk>/", views.course_detail_by_id, name="course_detail_by_id"),
    path("join/id/<int:pk>/", views.join_course_by_id, name="join_course_by_id"),

    # (اختياري) الإبقاء على القديمة
    path("course/<slug:code>/", views.course_detail, name="course_detail"),
    path("join/<slug:code>/", views.join_course, name="join_course"),
]
