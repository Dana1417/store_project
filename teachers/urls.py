from django.urls import path
from . import views

app_name = "teachers"

urlpatterns = [
    # =========================
    #   لوحة المعلّم
    # =========================
    path("dashboard/", views.teacher_dashboard, name="dashboard"),

    # =========================
    #   تفاصيل مقرر معيّن
    # =========================
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),

    # محاضرات ومراجع داخل مقرر
    path("course/<int:course_id>/lesson/add/", views.add_lesson, name="add_lesson"),
    path("course/<int:course_id>/resource/add/", views.add_resource, name="add_resource"),

    # =========================
    #   روابط Teams (للمعلّم)
    # =========================
    path("course/<int:course_id>/open-teams/", views.open_teams, name="open_teams"),
    path("course/<int:course_id>/teams/update/", views.update_teams_link, name="update_teams_link"),

    # =========================
    #   إدارة المقررات (للمشرف)
    # =========================
    path("subject/new/", views.create_subject, name="create_subject"),
    path("course/new/", views.create_course, name="create_course"),
]
