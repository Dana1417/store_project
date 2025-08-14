from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),            # /student/
    path("dashboard/", views.dashboard, name="dashboard"),  # /student/dashboard/

    path("courses/", views.my_courses, name="my_courses"),
    path("exams/", views.my_exams, name="my_exams"),
    path("certs/", views.my_certs, name="my_certs"),
    path("resources/", views.my_resources, name="my_resources"),
    path("profile/", views.my_profile, name="my_profile"),
]
