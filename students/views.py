# students/views.py
from __future__ import annotations

import re
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .models import Student, Enrollment, ExamResult, Certificate, Resource
from .permissions import student_required

# نماذج المعلّم لعرض تفاصيل المقرر/الدروس/المراجع
from teachers.models import Lesson, Resource as TResource


# =========================
#      أدوات مساعدة
# =========================
def _get_student(request) -> Student:
    """إرجاع/إنشاء سجل Student للمستخدم الحالي (آمن)."""
    student, _ = Student.objects.get_or_create(user=request.user)
    return student

def _norm_code(raw: str) -> str:
    """تنظيف slug/cod بدون حذف الشرطات حتى تدعمي قيماً مثل p2-."""
    return (raw or "").strip()


def _find_enrollment_by_code(student: Student, code: str):
    """
    يحاول إيجاد Enrollment نشط للطالبة عبر عدة محاولات آمنة:
    1) slug مطابق (غير حساس لحالة الأحرف)
    2) slug بعد إزالة الشرطات الطرفية (إن كان هناك شرطة زائدة)
    3) رقم -> اعتباره course_id
    """
    qs = (
        Enrollment.objects.select_related("course")
        .filter(student=student, status="active")
    )

    # 1) slug كما هو
    e = qs.filter(course__slug__iexact=code).first()
    if e:
        return e

    # 2) slug بعد إزالة الشرطات الطرفية فقط
    trimmed = code.strip("-")
    if trimmed and trimmed != code:
        e = qs.filter(course__slug__iexact=trimmed).first()
        if e:
            return e

    # 3) إن كان رقماً جرّب اعتباره course_id
    if code.isdigit():
        e = qs.filter(course_id=int(code)).first()
        if e:
            return e

    return None


# =========================
#       لوحة الطالب
# =========================
@student_required
@require_http_methods(["GET"])
def dashboard(request):
    s = _get_student(request)

    enrollments_qs = (
        s.enrollments
         .select_related("course")
         .filter(status="active")
         .order_by("-joined_at")
    )

    certs_qs = s.certificates.select_related("course").order_by("-issued_at")

    resources_qs = (
        Resource.objects
        .filter(
            Q(is_public=True) |
            Q(course__enrollments__student=s,
              course__enrollments__status="active")
        )
        .select_related("course")
        .distinct()
        .order_by("title")
    )

    ctx = {
        "student": s,
        "now": timezone.now(),
        "enrollments": enrollments_qs,
        "certs": certs_qs,
        "resources": resources_qs,
        "enroll_count": enrollments_qs.count(),
        "exam_count": s.exam_results.count(),
        "cert_count": certs_qs.count(),
        "res_count": resources_qs.count(),
    }
    return render(request, "students/dashboard.html", ctx)


# =========================
#        دوراتي
# =========================
@student_required
@require_http_methods(["GET"])
def my_courses(request):
    s = _get_student(request)
    enrollments = (
        s.enrollments
         .select_related("course")
         .filter(status="active")
         .order_by("-joined_at")
    )
    return render(
        request,
        "students/my_courses.html",
        {"student": s, "enrollments": enrollments, "now": timezone.now()},
    )


# =========================
#     نتائج الاختبارات
# =========================
@student_required
@require_http_methods(["GET"])
def my_exams(request):
    s = _get_student(request)
    results = (
        ExamResult.objects
        .select_related("exam", "exam__course")
        .filter(student=s)
        .order_by("-graded_at")
    )
    return render(request, "students/my_exams.html", {"student": s, "results": results})


# =========================
#        شهاداتي
# =========================
@student_required
@require_http_methods(["GET"])
def my_certs(request):
    s = _get_student(request)
    certs = s.certificates.select_related("course").order_by("-issued_at")
    return render(request, "students/my_certs.html", {"student": s, "certs": certs})


# =========================
#        مراجعـي
# =========================
@student_required
@require_http_methods(["GET"])
def my_resources(request):
    s = _get_student(request)
    resources = (
        Resource.objects
        .filter(
            Q(is_public=True) |
            Q(course__enrollments__student=s,
              course__enrollments__status="active")
        )
        .select_related("course")
        .distinct()
        .order_by("title")
    )
    return render(request, "students/my_resources.html", {"student": s, "resources": resources})


# =========================
#        ملفي الشخصي
# =========================
@csrf_protect
@student_required
@require_http_methods(["GET", "POST"])
def my_profile(request):
    s = _get_student(request)

    if request.method == "POST":
        phone = (request.POST.get("phone") or "").strip()
        city = (request.POST.get("city") or "").strip()

        phone_rx = re.compile(r"^\+?\d{8,15}$")
        if phone and not phone_rx.match(phone):
            messages.error(request, "رقم الجوال غير صحيح. مثال: +9665xxxxxxx")
            return redirect("students:my_profile")

        if len(city) > 120:
            messages.error(request, "اسم المدينة طويل جدًا.")
            return redirect("students:my_profile")

        if hasattr(s, "phone"):
            s.phone = phone
        if hasattr(s, "city"):
            s.city = city
        s.save()

        messages.success(request, "تم تحديث الملف الشخصي بنجاح.")
        return redirect("students:my_profile")

    return render(request, "students/my_profile.html", {"student": s})


# =========================
#  تفاصيل مقرر لطالب مُسجَّل (بالـ pk عبر Enrollment)
# =========================
@student_required
@require_http_methods(["GET"])
def course_detail_by_id(request, pk: int):
    s = _get_student(request)

    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course"),
        student=s,
        course_id=pk,
        status="active",
    )
    course = enrollment.course
    course_title = getattr(course, "title", None) or str(course)

    # الدروس/المراجع من جدول المعلّم (نحاول بالـ pk ثم الـ slug إن وجد)
    lessons = Lesson.objects.none()
    resources = TResource.objects.none()

    try:
        qs1 = Lesson.objects.filter(course_id=pk)
        slug = getattr(course, "slug", "") or ""
        qs2 = Lesson.objects.filter(course__slug=slug).exclude(id__in=qs1.values("id")) if slug else Lesson.objects.none()
        lessons = (qs1 | qs2).order_by("-published_at", "-id")
    except Exception:
        pass

    try:
        qs1 = TResource.objects.filter(course_id=pk)
        slug = getattr(course, "slug", "") or ""
        qs2 = TResource.objects.filter(course__slug=slug).exclude(id__in=qs1.values("id")) if slug else TResource.objects.none()
        resources = (qs1 | qs2).order_by("-created_at", "-id")
    except Exception:
        pass

    return render(
        request,
        "students/course_detail.html",
        {
            "course": course,
            "course_title": course_title,
            "lessons": lessons,
            "resources": resources,
            "now": timezone.now(),
        },
    )


# =========================
#   دخول الحصة (Teams) بالـ pk عبر Enrollment
# =========================
@student_required
@require_http_methods(["GET"])
def join_course_by_id(request, pk: int):
    s = _get_student(request)

    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course"),
        student=s,
        course_id=pk,
        status="active",
    )
    course = enrollment.course

    now = timezone.now()
    if getattr(enrollment, "starts_at", None) and now < enrollment.starts_at:
        messages.warning(request, "لم يبدأ موعد دورتك بعد.")
        return redirect("students:dashboard")
    if getattr(enrollment, "ends_at", None) and now > enrollment.ends_at:
        messages.warning(request, "انتهت صلاحية الوصول إلى هذه الدورة.")
        return redirect("students:dashboard")

    teams_link = getattr(enrollment, "teams_link", None) or getattr(course, "teams_link", None)
    if not teams_link:
        messages.error(request, "لا يوجد رابط متاح للحصة حالياً.")
        return redirect("students:dashboard")

    return redirect(teams_link)


# =========================
#  تفاصيل بالـ slug/code (فعليًا slug) لمن يستخدمه
# =========================
@student_required
@require_http_methods(["GET"])
def course_detail(request, code: str):
    s = _get_student(request)
    code = _norm_code(code)

    enrollment = _find_enrollment_by_code(s, code)
    if not enrollment:
        raise Http404("لم يتم العثور على المقرر لهذه الطالبة.")

    course = enrollment.course
    course_title = getattr(course, "title", None) or str(course)

    lessons = Lesson.objects.filter(course=course).order_by("-published_at", "-id")
    resources = TResource.objects.filter(course=course).order_by("-created_at", "-id")

    return render(
        request,
        "students/course_detail.html",
        {
            "course": course,
            "course_title": course_title,
            "lessons": lessons,
            "resources": resources,
            "now": timezone.now(),
        },
    )


# =========================
#   دخول الحصة عبر slug/code (ندعم slug فقط + محاولات مساعدة)
# =========================
@student_required
@require_http_methods(["GET"])
def join_course(request, code: str):
    s = _get_student(request)
    code = _norm_code(code)

    enrollment = _find_enrollment_by_code(s, code)
    if not enrollment:
        messages.error(request, "لا يوجد تسجيل نشط لهذه الدورة.")
        return redirect("students:dashboard")

    now = timezone.now()
    if getattr(enrollment, "starts_at", None) and now < enrollment.starts_at:
        messages.warning(request, "لم يبدأ موعد دورتك بعد.")
        return redirect("students:dashboard")
    if getattr(enrollment, "ends_at", None) and now > enrollment.ends_at:
        messages.warning(request, "انتهت صلاحية الوصول إلى هذه الدورة.")
        return redirect("students:dashboard")

    teams_link = getattr(enrollment, "teams_link", None) or getattr(enrollment.course, "teams_link", None)
    if not teams_link:
        messages.error(request, "لا يوجد رابط Teams متاح.")
        return redirect("students:dashboard")

    return redirect(teams_link)
