from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, Prefetch

from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from students.models import Enrollment
from store.models import Booking
from .models import TeacherProfile, Course, Lesson, Resource, Subject
from .forms import LessonForm, ResourceForm, SubjectForm, CourseForm

# (اختياري) Cloudinary Errors
try:
    from cloudinary.exceptions import Error as CloudinaryError
except Exception:
    class CloudinaryError(Exception):
        ...


# =========================
#  أدوات مساعدة
# =========================
def _get_teacher_profile(user) -> TeacherProfile | None:
    """إرجاع TeacherProfile للمستخدم الحالي."""
    tp = getattr(user, "teacher_profile", None) or getattr(user, "teacherprofile", None)
    if tp:
        return tp
    return TeacherProfile.objects.filter(user=user).first()


def _ensure_teacher(user) -> bool:
    """التحقق أن المستخدم معلّم."""
    return bool(_get_teacher_profile(user)) or getattr(user, "role", "") == "teacher"


def _require_https(url: str) -> str:
    """التحقق أن الرابط يبدأ بـ https://"""
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith("https://"):
        raise ValidationError("الرابط يجب أن يبدأ بـ https://")
    return url


# =========================
#  لوحة المعلّم
# =========================
@login_required
@require_http_methods(["GET"])
def teacher_dashboard(request: HttpRequest) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    if not tp:
        return HttpResponseForbidden("غير مصرّح")

    # عدّ الطلاب لكل كورس
    enroll_count_sq = (
        Enrollment.objects
        .filter(course_id=OuterRef("pk"))
        .values("course_id")
        .annotate(c=Count("id"))
        .values("c")[:1]
    )

    courses_qs = (
        Course.objects.filter(teacher=tp)
        .select_related("subject")
        .prefetch_related(
            Prefetch("lessons", queryset=Lesson.objects.only("id", "title", "order").order_by("order")),
            Prefetch("resources", queryset=Resource.objects.only("id", "title", "created_at", "kind").order_by("-id")),
        )
        .annotate(students_total=Subquery(enroll_count_sq))
        .order_by("-id")
    )

    # إحصائيات عامة
    total_courses = courses_qs.count()
    total_lessons = Lesson.objects.filter(course__teacher=tp).count()
    total_students = sum(c.students_total or 0 for c in courses_qs)

    courses_data = [
        {
            "id": c.id,
            "title": c.title,
            "subject": c.subject.name if c.subject_id else "",
            "stage": c.subject.stage if c.subject_id else "",
            "students": c.students_total or 0,
            "cover": getattr(c, "cover_image_url", "") or "",
            "detailUrl": reverse("teachers:course_detail", kwargs={"course_id": c.id}),
        }
        for c in courses_qs
    ]

    ctx = {
        "tp": tp,
        "teacher_name": request.user.get_full_name() or request.user.username,
        "courses": courses_qs,
        "courses_data": courses_data,
        "total_courses": total_courses,
        "total_lessons": total_lessons,
        "total_students": total_students,
    }
    return render(request, "teachers/dashboard.html", ctx)


# =========================
#  تفاصيل المقرر
# =========================
@login_required
@require_http_methods(["GET"])
def course_detail(request: HttpRequest, course_id: int) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    if not tp:
        return HttpResponseForbidden("غير مصرّح")

    course = get_object_or_404(
        Course.objects
        .select_related("subject", "teacher")
        .prefetch_related(
            Prefetch("lessons", queryset=Lesson.objects.order_by("order")),
            Prefetch("resources", queryset=Resource.objects.order_by("-id")),
        ),
        pk=course_id,
        teacher=tp,
    )

    enrollments = (
        Enrollment.objects
        .select_related("student__user")
        .filter(course_id=course.id)
        .order_by("-joined_at", "id")
    )

    ctx = {
        "course": course,
        "students": enrollments,
        "enrollments": enrollments,
        "lessons": course.lessons.all(),
        "resources": course.resources.all(),
        "teams_link_safe": course.teams_link if str(course.teams_link).startswith("https://") else "",
        "join_param": course.code or str(course.id),
    }
    return render(request, "teachers/course_detail.html", ctx)


# =========================
#  فتح Teams
# =========================
@login_required
@require_http_methods(["GET"])
def open_teams(request: HttpRequest, course_id: int) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")
    tp = _get_teacher_profile(request.user)
    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    link = (course.teams_link or "").strip()
    if not link:
        messages.error(request, "لا يوجد رابط Teams لهذا المقرر.")
        return redirect("teachers:course_detail", course_id=course.id)
    if not link.startswith("https://"):
        messages.error(request, "رابط Teams غير آمن.")
        return redirect("teachers:course_detail", course_id=course.id)

    return redirect(link)


# =========================
#  تحديث Teams
# =========================
@login_required
@require_http_methods(["POST"])
def update_teams_link(request: HttpRequest, course_id: int) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")
    tp = _get_teacher_profile(request.user)
    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    raw = request.POST.get("teams_link", "")
    try:
        course.teams_link = _require_https(raw)
        course.save(update_fields=["teams_link"])
        messages.success(request, "تم تحديث الرابط بنجاح.")
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect("teachers:course_detail", course_id=course.id)


# =========================
#  إضافة محاضرة
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def add_lesson(request: HttpRequest, course_id: int) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")
    tp = _get_teacher_profile(request.user)
    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    if request.method == "POST":
        form = LessonForm(request.POST, request.FILES)
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


# =========================
#  إضافة مرجع
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def add_resource(request: HttpRequest, course_id: int) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")
    tp = _get_teacher_profile(request.user)
    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course = course
            obj.save()
            messages.success(request, "✅ تم إضافة المرجع.")
            return redirect("teachers:course_detail", course_id=course.id)
        messages.error(request, "تحقّقي من الحقول.")
    else:
        form = ResourceForm()

    return render(request, "teachers/resource_form.html", {"form": form, "course": course})


# =========================
#  إنشاء مادة (للمشرف)
# =========================
@login_required
@transaction.atomic
@require_http_methods(["GET", "POST"])
def create_subject(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return HttpResponseForbidden("خاص بالمشرف.")

    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ تم إنشاء المادة.")
            return redirect("teachers:create_course")
    else:
        form = SubjectForm()

    return render(request, "teachers/subject_form.html", {"form": form})


# =========================
#  إنشاء كورس (للمشرف)
# =========================
@login_required
@transaction.atomic
@require_http_methods(["GET", "POST"])
def create_course(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return HttpResponseForbidden("خاص بالمشرف.")
    tp = _get_teacher_profile(request.user)

    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            if not course.teacher_id and tp:
                course.teacher = tp
            course.is_active = True
            course.save()
            messages.success(request, "✅ تم إنشاء الكورس.")
            return redirect("teachers:course_detail", course_id=course.id)
    else:
        form = CourseForm()

    if not Subject.objects.exists():
        messages.info(request, "ℹ️ أنشئ مادة أولًا.")
        return redirect("teachers:create_subject")

    return render(request, "teachers/course_form.html", {"form": form})


# =========================
#  حجوزات المعلّم
# =========================
@login_required
@require_http_methods(["GET"])
def teacher_bookings(request: HttpRequest) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")
    tp = _get_teacher_profile(request.user)

    bookings = (
        Booking.objects
        .filter(course__teacher=tp)
        .select_related("course")
        .order_by("-created_at")
    )

    return render(request, "teachers/bookings.html", {"bookings": bookings})
