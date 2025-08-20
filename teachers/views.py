from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, Prefetch

# ✅ إصلاح استيراد الأنواع (لإنهاء تحذير Pylance)
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseForbidden

from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from students.models import Enrollment
from .models import TeacherProfile, Course, Lesson, Resource, Subject
from .forms import LessonForm, ResourceForm, SubjectForm, CourseForm

# (اختياري) توضيح أخطاء Cloudinary القادمة من التخزين
try:
    from cloudinary.exceptions import Error as CloudinaryError
except Exception:
    class CloudinaryError(Exception):
        ...


# =========================
#  أدوات مساعدة داخلية
# =========================
def _get_teacher_profile(user) -> TeacherProfile | None:
    """إرجاع TeacherProfile للمستخدم (يدعم اختلاف related_name)."""
    tp = getattr(user, "teacher_profile", None) or getattr(user, "teacherprofile", None)
    if tp:
        return tp
    return TeacherProfile.objects.filter(user=user).first()


def _ensure_teacher(user) -> bool:
    """التحقق أن المستخدم معلّم (أو يملك TeacherProfile)."""
    return bool(_get_teacher_profile(user)) or getattr(user, "role", "") == "teacher"


def _require_https(url: str) -> str:
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
            Prefetch(
                "lessons",
                queryset=Lesson.objects.only("id", "title", "published_at", "order").order_by("order"),
            ),
            Prefetch(
                "resources",
                queryset=Resource.objects.only("id", "title", "created_at", "kind").order_by("-id"),
            ),
        )
        .annotate(students_total=Subquery(enroll_count_sq))
        .order_by("-id")
    )

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
        "courses": courses_qs,
        "teacher_name": request.user.get_full_name() or request.user.username,
        "courses_data": courses_data,
    }
    return render(request, "teachers/dashboard.html", ctx)


# =========================
#  تفاصيل المقرر (للمعلّم)
# =========================
@login_required
@require_http_methods(["GET"])
def course_detail(request: HttpRequest, course_id: int) -> HttpResponse:
    """صفحة تفاصيل الكورس للمعلّم الحالي."""
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

    lessons_qs = course.lessons.all()
    resources_qs = course.resources.all()

    teams_link_safe = ""
    if getattr(course, "teams_link", "") and str(course.teams_link).startswith("https://"):
        teams_link_safe = course.teams_link

    course.enrollment_list = list(enrollments)

    ctx = {
        "course": course,
        "students": enrollments,
        "enrollments": enrollments,
        "lessons": lessons_qs,
        "resources": resources_qs,
        "teams_link_safe": teams_link_safe,
        "join_param": course.code or str(course.id),
    }
    return render(request, "teachers/course_detail.html", ctx)


# =========================
#  فتح Teams من صفحة المعلم
# =========================
@login_required
@require_http_methods(["GET"])
def open_teams(request: HttpRequest, course_id: int) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    if not tp:
        return HttpResponseForbidden("غير مصرّح")

    course = get_object_or_404(Course, pk=course_id, teacher=tp)
    link = (getattr(course, "teams_link", "") or "").strip()

    if not link:
        messages.error(request, "لا يوجد رابط Teams لهذا المقرر.")
        return redirect("teachers:course_detail", course_id=course.id)

    if not link.startswith("https://"):
        messages.error(request, "رابط Teams غير آمن. يجب أن يبدأ بـ https://")
        return redirect("teachers:course_detail", course_id=course.id)

    return redirect(link)


# =========================
#  تحديث رابط Teams من صفحة المقرر
# =========================
@login_required
@require_http_methods(["POST"])
def update_teams_link(request: HttpRequest, course_id: int) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    if not tp:
        return HttpResponseForbidden("غير مصرّح")

    course = get_object_or_404(Course, pk=course_id, teacher=tp)
    raw = request.POST.get("teams_link", "")

    try:
        course.teams_link = _require_https(raw)
        course.save(update_fields=["teams_link"])
        messages.success(request, "تم تحديث رابط Teams بنجاح.")
    except ValidationError as e:
        messages.error(request, str(e))
    except Exception:
        messages.error(request, "تعذّر تحديث رابط Teams. حاولي مرة أخرى.")

    return redirect("teachers:course_detail", course_id=course.id)


# =========================
#  إنشاء محاضرة داخل مقرر
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def add_lesson(request: HttpRequest, course_id: int) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    if not tp:
        return HttpResponseForbidden("غير مصرّح")

    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    if request.method == "POST":
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course_id = course.id
            try:
                obj.full_clean()
                obj.save()
            except CloudinaryError as ce:
                messages.error(request, f"تعذّر رفع الملف إلى Cloudinary: {ce}")
                return render(request, "teachers/lesson_form.html", {"form": form, "course": course})
            except ValidationError as ve:
                if hasattr(ve, "message_dict"):
                    for field, errs in ve.message_dict.items():
                        for e in errs:
                            messages.error(request, f"{field}: {e}")
                else:
                    messages.error(request, str(ve))
                return render(request, "teachers/lesson_form.html", {"form": form, "course": course})
            messages.success(request, "✅ تم إضافة المحاضرة.")
            return redirect("teachers:course_detail", course_id=course.id)
        messages.error(request, "تحقّقي من الحقول.")
    else:
        form = LessonForm()

    return render(request, "teachers/lesson_form.html", {"form": form, "course": course})


# =========================
#  إضافة مرجع/كتاب داخل مقرر
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def add_resource(request: HttpRequest, course_id: int) -> HttpResponse:
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    if not tp:
        return HttpResponseForbidden("غير مصرّح")

    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course_id = course.id
            try:
                obj.full_clean()
                obj.save()
            except CloudinaryError as ce:
                messages.error(request, f"تعذّر رفع الملف إلى Cloudinary: {ce}")
                return render(request, "teachers/resource_form.html", {"form": form, "course": course})
            except ValidationError as ve:
                if hasattr(ve, "message_dict"):
                    for field, errs in ve.message_dict.items():
                        for e in errs:
                            messages.error(request, f"{field}: {e}")
                else:
                    messages.error(request, str(ve))
                return render(request, "teachers/resource_form.html", {"form": form, "course": course})
            messages.success(request, "✅ تم إضافة المرجع/الكتاب.")
            return redirect("teachers:course_detail", course_id=course.id)
        messages.error(request, "تحقّقي من الحقول.")
    else:
        form = ResourceForm()

    return render(request, "teachers/resource_form.html", {"form": form, "course": course})


# =========================
#  إنشاء مادة (Subject) — للمشرف
# =========================
@login_required
@transaction.atomic
@require_http_methods(["GET", "POST"])
def create_subject(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return HttpResponseForbidden("الإنشاء مخصّص للمشرف.")

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


# =========================
#  إنشاء كورس — للمشرف
# =========================
@login_required
@transaction.atomic
@require_http_methods(["GET", "POST"])
def create_course(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return HttpResponseForbidden("الإنشاء مخصّص للمشرف.")

    tp = _get_teacher_profile(request.user)

    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            if not getattr(course, "teacher_id", None) and tp:
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
