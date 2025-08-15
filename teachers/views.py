# teachers/views.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import OuterRef, Subquery, Count

from .models import Course, TeacherProfile, Subject
from .forms import LessonForm, ResourceForm, SubjectForm, CourseForm
from students.models import Enrollment


def _get_teacher_profile(user) -> TeacherProfile | None:
    tp = getattr(user, "teacher_profile", None) or getattr(user, "teacherprofile", None)
    if tp:
        return tp
    return TeacherProfile.objects.filter(user=user).first()


def _ensure_teacher(user) -> bool:
    return getattr(user, "role", "") == "teacher" and _get_teacher_profile(user) is not None


@login_required
def teacher_dashboard(request):
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)

    enroll_count_sq = (
        Enrollment.objects.filter(course=OuterRef("pk"))
        .values("course")
        .annotate(c=Count("id"))
        .values("c")[:1]
    )

    courses = (
        Course.objects.filter(teacher=tp)
        .select_related("subject")
        .prefetch_related("lessons", "resources")
        .annotate(students_count=Subquery(enroll_count_sq))
        .order_by("-id")
    )

    courses_data = [
        {
            "id": c.id,
            "title": c.title,
            "subject": c.subject.name if c.subject_id else "",
            "stage": c.subject.stage if c.subject_id else "",
            "students": c.students_count or 0,
            "cover": getattr(c, "cover_image_url", "") or "",
            "detailUrl": f"/teachers/course/{c.id}/",
        }
        for c in courses
    ]

    ctx = {
        "tp": tp,
        "courses": courses,
        "teacher_name": request.user.get_full_name() or request.user.username,
        "courses_data": courses_data,
    }
    return render(request, "teachers/dashboard.html", ctx)


@login_required
def course_detail(request, course_id: int):
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    course = get_object_or_404(
        Course.objects.select_related("subject", "teacher"),
        pk=course_id,
        teacher=tp,
    )

    enrollments = Enrollment.objects.filter(course=course).select_related("student__user")
    students = [en.student.user for en in enrollments]

    return render(request, "teachers/course_detail.html", {"course": course, "students": students})


@login_required
def add_lesson(request, course_id: int):
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course = course
            obj.save()
            messages.success(request, "✅ تم إضافة المحاضرة.")
            return redirect("teachers:course_detail", course_id=course.id)
        messages.error(request, "تحقّقي من الحقول.")
    else:
        form = LessonForm()

    return render(request, "teachers/lesson_form.html", {"form": form, "course": course})


@login_required
def add_resource(request, course_id: int):
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    if request.method == "POST":
        form = ResourceForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course = course
            obj.save()
            messages.success(request, "✅ تم إضافة المرجع/الكتاب.")
            return redirect("teachers:course_detail", course_id=course.id)
        messages.error(request, "تحقّقي من الحقول.")
    else:
        form = ResourceForm()

    return render(request, "teachers/resource_form.html", {"form": form, "course": course})


@login_required
@transaction.atomic
def create_subject(request):
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ تم إنشاء المادة بنجاح.")
            return redirect("teachers:create_course")
        messages.error(request, "تحقّقي من الحقول.")
    else:
        form = SubjectForm()

    return render(request, "teachers/subject_form.html", {"form": form})


@login_required
@transaction.atomic
def create_course(request):
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)

    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = tp
            if not getattr(course, "is_active", True):
                course.is_active = True
            course.save()
            messages.success(request, "✅ تم إنشاء الكورس بنجاح.")
            return redirect("teachers:course_detail", course_id=course.id)
        messages.error(request, "تحقّقي من الحقول.")
    else:
        form = CourseForm()

    if not Subject.objects.exists():
        messages.info(request, "ℹ️ لا توجد مواد بعد — أنشئي مادة جديدة أولًا.")
        return redirect("teachers:create_subject")

    return render(request, "teachers/course_form.html", {"form": form})
