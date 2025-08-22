from django.shortcuts import render
from store.models import Booking
from students.models import Student
from teachers.models import TeacherProfile, Course

def dashboard(request):
    return render(request, "adminpanel/dashboard.html")

def bookings_list(request):
    bookings = Booking.objects.all().order_by("-created_at")
    return render(request, "adminpanel/bookings_list.html", {"bookings": bookings})

def students_list(request):
    students = Student.objects.all()
    return render(request, "adminpanel/students_list.html", {"students": students})

def teachers_list(request):
    teachers = TeacherProfile.objects.all()
    return render(request, "adminpanel/teachers_list.html", {"teachers": teachers})

def courses_list(request):
    courses = Course.objects.all()
    return render(request, "adminpanel/courses_list.html", {"courses": courses})
