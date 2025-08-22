from __future__ import annotations

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import Student, Enrollment, ExamResult, Certificate, Resource
from teachers.models import Lesson, Course
from .permissions import student_required


# =========================
#        مساعد الطالب
# =========================
def _get_student(request) -> Student:
    """
    إرجاع/إنشاء سجل Student للمستخدم الحالي.
    يمنع الأخطاء إذا الطالب أول مرة يدخل.
    """
    student, _ = Student.objects.get_or_create(user=request.user)
    return student


# =========================
#       لوحة الطالب
# =========================
@student_required
@require_http_methods(["GET"])
def dashboard(request):
    """لوحة الطالب: المقررات + الموارد + الشهادات + الامتحانات"""
    student = _get_student(request)

    enrollments = student.enrollments.select_related("course")
    resources = Resource.objects.filter(course__in=enrollments.values("course_id"))
    certs = student.certificates.select_related("course")
    exams = ExamResult.objects.filter(student=student).select_related("exam", "exam__course")

    return render(request, "students/dashboard.html", {
        "student": student,
        "enrollments": enrollments,
        "resources": resources,
        "certs": certs,
        "exams": exams,
    })


# =========================
#       مقرراتي
# =========================
@student_required
def my_courses(request):
    student = _get_student(request)
    enrollments = student.enrollments.select_related("course")
    return render(request, "students/my_courses.html", {"enrollments": enrollments})


# =========================
#       امتحاناتي
# =========================
@student_required
def my_exams(request):
    student = _get_student(request)
    results = ExamResult.objects.filter(student=student).select_related("exam", "exam__course")
    return render(request, "students/my_exams.html", {"results": results})


# =========================
#       شهاداتي
# =========================
@student_required
def my_certs(request):
    student = _get_student(request)
    certs = student.certificates.select_related("course")
    return render(request, "students/my_certs.html", {"certs": certs})


# =========================
#       مواردي
# =========================
@student_required
def my_resources(request):
    student = _get_student(request)
    enrollments = student.enrollments.select_related("course")
    resources = Resource.objects.filter(course__in=enrollments.values("course_id"))
    return render(request, "students/my_resources.html", {"resources": resources})


# =========================
#       الملف الشخصي
# =========================
@student_required
def my_profile(request):
    student = _get_student(request)
    return render(request, "students/my_profile.html", {"student": student})


# =========================
#      تفاصيل مقرر (slug)
# =========================
@student_required
def course_detail(request, code: str):
    """
    عرض تفاصيل مقرر عبر slug.
    يتحقق أن الطالب مسجّل فيه.
    """
    student = _get_student(request)
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course"),
        course__slug=code,
        student=student,
    )
    course = enrollment.course
    lessons = Lesson.objects.filter(course_id=course.id).order_by("order", "id")
    resources = Resource.objects.filter(course_id=course.id).order_by("-created_at")

    return render(request, "students/course_detail.html", {
        "enrollment": enrollment,
        "course": course,
        "lessons": lessons,
        "resources": resources,
    })


# =========================
#      تفاصيل مقرر (id)
# =========================
@student_required
def course_detail_by_id(request, pk: int):
    """
    عرض تفاصيل مقرر عبر id (للتوافق/الإدارة).
    """
    student = _get_student(request)
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course"),
        course__id=pk,
        student=student,
    )
    course = enrollment.course
    lessons = Lesson.objects.filter(course_id=course.id).order_by("order", "id")
    resources = Resource.objects.filter(course_id=course.id).order_by("-created_at")

    return render(request, "students/course_detail.html", {
        "enrollment": enrollment,
        "course": course,
        "lessons": lessons,
        "resources": resources,
    })


# =========================
#        انضمام لمقرر
# =========================
@student_required
def join_course(request, code: str):
    """انضمام لمقرر عبر slug."""
    student = _get_student(request)
    course = get_object_or_404(Course, slug=code)

    enrollment, created = Enrollment.objects.get_or_create(student=student, course=course)
    if created:
        messages.success(request, f"🎉 تم انضمامك للمقرر «{course.title}».")
    else:
        messages.info(request, f"ℹ️ أنت مسجل مسبقًا في «{course.title}».")

    return redirect("students:course_detail", code=course.slug)


@student_required
def join_course_by_id(request, pk: int):
    """انضمام لمقرر عبر id (اختياري)."""
    student = _get_student(request)
    course = get_object_or_404(Course, id=pk)

    enrollment, created = Enrollment.objects.get_or_create(student=student, course=course)
    if created:
        messages.success(request, f"🎉 تم انضمامك للمقرر «{course.title}».")
    else:
        messages.info(request, f"ℹ️ أنت مسجل مسبقًا في «{course.title}».")

    return redirect("students:course_detail_by_id", pk=course.id)
