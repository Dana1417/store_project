# teachers/views.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, Prefetch
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from students.models import Enrollment
from .models import TeacherProfile, Course, Lesson, Resource, Subject
from .forms import LessonForm, ResourceForm, SubjectForm, CourseForm


# =========================
#  أدوات مساعدة داخلية
# =========================
def _get_teacher_profile(user) -> TeacherProfile | None:
    """
    إرجاع TeacherProfile للمستخدم (يدعم اختلاف related_name).
    """
    tp = getattr(user, "teacher_profile", None) or getattr(user, "teacherprofile", None)
    if tp:
        return tp
    return TeacherProfile.objects.filter(user=user).first()


def _ensure_teacher(user) -> bool:
    """
    التحقق أن المستخدم معلّم (أو يملك TeacherProfile).
    عدّلي حسب نظام الصلاحيات لديك (بعض الأنظمة تحفظ role = 'teacher').
    """
    return bool(_get_teacher_profile(user)) or getattr(user, "role", "") == "teacher"


# =========================
#  لوحة المعلّم
# =========================
@login_required
@require_http_methods(["GET"])
def teacher_dashboard(request):
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    if not tp:
        return HttpResponseForbidden("غير مصرّح")

    # Subquery لعدّ الطلاب المسجّلين بكل مقرر (نستخدم course_id لتفادي اختلاف نوع Course)
    enroll_count_sq = (
        Enrollment.objects
        .filter(course_id=OuterRef("pk"))
        .values("course_id")
        .annotate(c=Count("id"))
        .values("c")[:1]
    )

    # مقررات المعلّم + تهيئة العلاقات اللازمة للعرض
    courses_qs = (
        Course.objects.filter(teacher=tp)
        .select_related("subject")
        .prefetch_related(
            Prefetch("lessons", queryset=Lesson.objects.only("id", "title", "published_at", "order").order_by("order")),
            Prefetch("resources", queryset=Resource.objects.only("id", "title", "created_at", "kind").order_by("-id")),
        )
        .annotate(students_total=Subquery(enroll_count_sq))  # لا تتعارض مع أي @property مسماه students_count
        .order_by("-id")
    )

    # بيانات خفيفة للواجهة (إن أردتِ JSON/JS)
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
#  تفاصيل المقرر
# =========================
@login_required
@require_http_methods(["GET"])
def course_detail(request, course_id: int):
    """
    صفحة تفاصيل الكورس:
    - تجلب كائن الكورس نفسه (Course instance) خاص بالمعلّم الحالي
    - تجلب قائمة التسجيلات Enrollment باستخدام course_id لتفادي أخطاء النوع
    - تجهّز علاقات lessons/resources لتحسين الأداء
    """
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
        teacher=tp,  # يضمن أن المقرر يخص هذا المعلّم
    )

    # ✅ نستخدم course_id بدل course لتفادي ValueError عند اختلاف نوع Course
    enrollments = (
        Enrollment.objects
        .select_related("student__user")
        .filter(course_id=course.id)
        .order_by("-joined_at", "id")
    )

    # البعض يستخدم في القالب course.enrollment_list — نوفّرها توافقًا
    course.enrollment_list = list(enrollments)

    ctx = {
        "course": course,
        "students": enrollments,     # توافقًا مع قوالب قديمة
        "enrollments": enrollments,  # الاسم الصريح
    }
    return render(request, "teachers/course_detail.html", ctx)


# =========================
#  إنشاء محاضرة داخل مقرر
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def add_lesson(request, course_id: int):
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    if not tp:
        return HttpResponseForbidden("غير مصرّح")

    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    if request.method == "POST":
        # مهم: تمرير request.FILES لدعم رفع الملفات (video_file/slide_file)
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course_id = course.id  # آمن وسريع
            obj.save()
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
def add_resource(request, course_id: int):
    if not _ensure_teacher(request.user):
        return HttpResponseForbidden("غير مصرّح")

    tp = _get_teacher_profile(request.user)
    if not tp:
        return HttpResponseForbidden("غير مصرّح")

    course = get_object_or_404(Course, pk=course_id, teacher=tp)

    if request.method == "POST":
        # مهم: تمرير request.FILES لأن Resource قد يدعم ملفًا
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course_id = course.id  # آمن وسريع
            obj.save()
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
def create_subject(request):
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
def create_course(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("الإنشاء مخصّص للمشرف.")

    # إن كان للمشرف TeacherProfile سيُستخدم افتراضيًا لو لم يحدَّد معلّم في الفورم
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
