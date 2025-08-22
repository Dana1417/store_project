from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),   # صفحة رئيسية للوحة المشرف
    path("bookings/", views.bookings_list, name="bookings_list"),
    path("students/", views.students_list, name="students_list"),
    path("teachers/", views.teachers_list, name="teachers_list"),
    path("courses/", views.courses_list, name="courses_list"),
]
