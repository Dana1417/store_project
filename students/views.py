# students/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from .models import Student, Enrollment, ExamResult, Certificate, Resource
from .permissions import student_required


def _get_student(request):
    """
    إرجاع/إنشاء سجل Student للمستخدم الحالي (آمن).
    يمنع أخطاء من نوع 'No Student matches the given query'.
    """
    student, _ = Student.objects.get_or_create(user=request.user)
    return student


@student_required
def dashboard(request):
    """
    لوحة الطالب:
    - عدّادات الدورات/الاختبارات/الشهادات/المراجع
    - قائمة الدورات المسجّلة عبر Enrollment
    - قائمة الشهادات
    - قائمة المراجع (عامة + الخاصة بدورات الطالب)
    """
    s = _get_student(request)

    # الدورات المسجّلة
    enrollments = (
        s.enrollments
        .select_related("course")
        .order_by("-joined_at")
    )

    # الشهادات
    certs = (
        s.certificates
        .select_related("course")
        .order_by("-issued_at")
    )

    # الموارد: نستخدم Q لدمج الشروط ثم distinct مرّة واحدة (حلّ للخطأ السابق)
    resources_qs = (
        Resource.objects.filter(
            Q(is_public=True) | Q(course__enrollments__student=s)
        )
        .select_related("course")
        .distinct()
        .order_by("title")
    )

    ctx = {
        "student": s,
        # العدّادات
        "enroll_count": enrollments.count(),
        "exam_count": s.exam_results.count(),
        "cert_count": certs.count(),
        "res_count": resources_qs.count(),
        # القوائم
        "enrollments": enrollments,
        "certs": certs,
        "resources": resources_qs,
    }
    # يستعمل القالب الموجود لديك ضمن مجلد store
    return render(request, "store/student_dashboard.html", ctx)


@student_required
def my_courses(request):
    """صفحة الدورات الخاصة بالطالب."""
    s = _get_student(request)
    enrollments = (
        s.enrollments
        .select_related("course")
        .order_by("-joined_at")
    )
    return render(request, "students/my_courses.html", {"enrollments": enrollments})


@student_required
def my_exams(request):
    """صفحة نتائج اختبارات الطالب."""
    s = _get_student(request)
    results = (
        ExamResult.objects
        .select_related("exam", "exam__course")
        .filter(student=s)
        .order_by("-graded_at")
    )
    return render(request, "students/my_exams.html", {"results": results})


@student_required
def my_certs(request):
    """صفحة شهادات الطالب."""
    s = _get_student(request)
    certs = (
        s.certificates
        .select_related("course")
        .order_by("-issued_at")
    )
    return render(request, "students/my_certs.html", {"certs": certs})


@student_required
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
    return render(request, "students/my_resources.html", {"resources": resources})


@student_required
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
