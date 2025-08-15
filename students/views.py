# students/views.py
from __future__ import annotations

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Student, Enrollment, ExamResult, Certificate, Resource
from .permissions import student_required


# =========================
#        مساعد الطالب
# =========================
def _get_student(request) -> Student:
    """
    إرجاع/إنشاء سجل Student للمستخدم الحالي (آمن).
    يمنع أخطاء من نوع 'No Student matches the given query'.
    """
    student, _ = Student.objects.get_or_create(user=request.user)
    return student


# =========================
#       لوحة الطالب
# =========================
@student_required
@require_http_methods(["GET"])
def dashboard(request):
    """
    لوحة الطالب:
    - عدّادات الدورات/الاختبارات/الشهادات/المراجع
    - قائمة الدورات المسجّلة عبر Enrollment
    - قائمة الشهادات
    - قائمة المراجع (عامة + الخاصة بدورات الطالب)
    """
    s = _get_student(request)

    # الدورات المسجّلة (أحدث انضمام أولاً)
    enrollments_qs = (
        s.enrollments
        .select_related("course")                # course مرجَع مباشر
        .order_by("-joined_at")
    )

    # الشهادات
    certs_qs = (
        s.certificates
        .select_related("course")
        .order_by("-issued_at")
    )

    # الموارد: عامة + موارد دورات الطالب
    resources_qs = (
        Resource.objects.filter(
            Q(is_public=True) | Q(course__enrollments__student=s)
        )
        .select_related("course")
        .distinct()                              # لمنع التكرار مع الـ OR
        .order_by("title")
    )

    # العدّادات (count() مباشر على الـ QuerySet لتقليل الذاكرة)
    ctx = {
        "student": s,
        "now": timezone.now(),                   # مفيد لعرض الحالة الزمنية في القالب
        "enrollments": enrollments_qs,
        "certs": certs_qs,
        "resources": resources_qs,

        "enroll_count": enrollments_qs.count(),
        "exam_count": s.exam_results.count(),
        "cert_count": certs_qs.count(),
        "res_count": resources_qs.count(),
    }

    # القالب الحالي لديك داخل مجلد store
    return render(request, "store/student_dashboard.html", ctx)


# =========================
#        دوراتي
# =========================
@student_required
@require_http_methods(["GET"])
def my_courses(request):
    """صفحة الدورات الخاصة بالطالب."""
    s = _get_student(request)
    enrollments = (
        s.enrollments
        .select_related("course")
        .order_by("-joined_at")
    )
    return render(request, "students/my_courses.html", {"student": s, "enrollments": enrollments, "now": timezone.now()})


# =========================
#     نتائج الاختبارات
# =========================
@student_required
@require_http_methods(["GET"])
def my_exams(request):
    """صفحة نتائج اختبارات الطالب."""
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
    """صفحة شهادات الطالب."""
    s = _get_student(request)
    certs = (
        s.certificates
        .select_related("course")
        .order_by("-issued_at")
    )
    return render(request, "students/my_certs.html", {"student": s, "certs": certs})


# =========================
#        مراجعـي
# =========================
@student_required
@require_http_methods(["GET"])
def my_resources(request):
    """صفحة المراجع (العامة + الخاصة بدورات الطالب)."""
    s = _get_student(request)
    resources = (
        Resource.objects.filter(
            Q(is_public=True) | Q(course__enrollments__student=s)
        )
        .select_related("course")
        .distinct()
        .order_by("title")
    )
    return render(request, "students/my_resources.html", {"student": s, "resources": resources})


# =========================
#       ملفي الشخصي
# =========================
@student_required
@require_http_methods(["GET", "POST"])
def my_profile(request):
    """تحديث بسيط لبيانات الطالب."""
    s = _get_student(request)

    if request.method == "POST":
        phone = (request.POST.get("phone") or "").strip()
        city = (request.POST.get("city") or "").strip()

        # تحقّق إدخال بسيط
        if len(phone) > 20 or len(city) > 120:
            messages.error(request, "المدخلات غير صحيحة.")
        else:
            s.phone = phone
            s.city = city
            s.save()
            messages.success(request, "تم تحديث البيانات.")
            return redirect("students:my_profile")

    return render(request, "students/my_profile.html", {"student": s})


# =========================
#   دخول الحصة (Teams) اختياري
# =========================
@student_required
@require_http_methods(["GET"])
def join_course(request, course_id: int):
    """
    يحاول إدخال الطالب إلى رابط الحصة للدورة المحددة بعد التحقق:
    - وجود تسجيل Enrollment للطالب في الدورة.
    - (اختياري) التحقق من الحالة الزمنية إن كانت موجودة.
    - وجود رابط teams_link على مستوى Enrollment أو course.
    """
    s = _get_student(request)

    # نضمن وجود تسجيل للطالب في هذه الدورة
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course"),
        student=s,
        course_id=course_id,
    )

    # تحقق زمني اختياري إن كانت الحقول موجودة
    now = timezone.now()
    starts_at = getattr(enrollment, "starts_at", None)
    ends_at = getattr(enrollment, "ends_at", None)
    status = getattr(enrollment, "status", "active")

    # لو عندك حالات، نسمح فقط للنشط
    if status not in ("active", None, ""):
        messages.error(request, "هذه الدورة ليست مفعلة لحسابك حالياً.")
        return redirect("students:dashboard")

    if starts_at and now < starts_at:
        messages.warning(request, "لم يبدأ موعد دورتك بعد.")
        return redirect("students:dashboard")

    if ends_at and now > ends_at:
        messages.warning(request, "انتهت صلاحية الوصول إلى هذه الدورة.")
        return redirect("students:dashboard")

    # جلب الرابط من enrollment ثم من course كخيار بديل
    teams_link = getattr(enrollment, "teams_link", None) or getattr(enrollment.course, "teams_link", None)
    if not teams_link:
        messages.error(request, "لا يوجد رابط متاح للحصة حالياً.")
        return redirect("students:dashboard")

    # إعادة توجيه آمنة إلى الرابط (خارج الموقع)
    return redirect(teams_link)
