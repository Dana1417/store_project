# students/urls.py
from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    # ======================
    #       لوحة الطالب
    # ======================
    path("dashboard/", views.dashboard, name="dashboard"),

    # ======================
    #       مقررات الطالب
    # ======================
    path("courses/", views.my_courses, name="my_courses"),

    # ======================
    #       امتحاناتي
    # ======================
    path("exams/", views.my_exams, name="my_exams"),

    # ======================
    #       شهاداتي
    # ======================
    path("certificates/", views.my_certs, name="my_certs"),

    # ======================
    #       مراجع المقررات
    # ======================
    path("resources/", views.my_resources, name="my_resources"),

    # ======================
    #       الملف الشخصي
    # ======================
    path("profile/", views.my_profile, name="my_profile"),

    # ======================
    #      تفاصيل المقرر
    # ======================
    # الوصول للمقرر عبر code (أساسي)
    path("course/<slug:code>/", views.course_detail, name="course_detail"),
    # مسار إضافي (اختياري) للـ id - يستخدم فقط للـ admin/debug
    path("course/id/<int:pk>/", views.course_detail_by_id, name="course_detail_by_id"),

    # ======================
    #       الانضمام للمقرر
    # ======================
    # الانضمام عبر code (أساسي)
    path("join/<slug:code>/", views.join_course, name="join_course"),
    # مسار إضافي للـ id (للإدارة فقط)
    path("join/id/<int:pk>/", views.join_course_by_id, name="join_course_by_id"),
]
