from __future__ import annotations

import re
from typing import List, Dict, Any, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.utils.text import slugify

from datetime import timedelta

from .models import Product

# نماذج الطلاب (للتفعيل بعد التأكيد)
from students.models import Student, Enrollment, Course

# نمط تحقق بسيط لرقم الجوال: + اختياري و 8-15 رقم
PHONE_RX = re.compile(r'^\+?\d{8,15}$')


# =========================
#     أدوات السلة (Session)
# =========================
def _cart_get(request) -> Dict[str, int]:
    """إرجاع سلة الجلسة الحالية كقاموس product_id -> quantity."""
    return request.session.get("cart", {})


def _cart_save(request, cart: Dict[str, int]) -> None:
    """حفظ السلة وتحديد modified لضمان حفظ الجلسة."""
    request.session["cart"] = cart
    request.session.modified = True


def _cart_add(request, product_id: int, qty: int = 1) -> None:
    """إضافة/زيادة كمية عنصر في السلة."""
    cart = _cart_get(request)
    pid = str(product_id)
    cart[pid] = max(1, int(cart.get(pid, 0)) + int(qty))
    _cart_save(request, cart)


def _cart_remove(request, product_id: int) -> None:
    """إزالة عنصر من السلة."""
    cart = _cart_get(request)
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        _cart_save(request, cart)


# =========================
#        المنتجات
# =========================
@require_http_methods(["GET"])
def product_list(request):
    products = Product.objects.filter(available=True).order_by("-created_at")
    return render(request, "store/product_list.html", {"products": products})


@require_http_methods(["GET"])
def product_detail(request, pk: int):
    product = get_object_or_404(Product, pk=pk, available=True)
    return render(request, "store/product_detail.html", {"product": product})


# =========================
#          السلة
# =========================
@require_http_methods(["POST"])
def add_to_cart(request, pk: int):
    """
    إضافة منتج إلى السلة (Session) عبر POST فقط.
    يدعم:
      - quantity: رقم صحيح 1..20 (افتراضي 1)
      - next: رابط داخلي لإعادة التوجيه بعد الإضافة (اختياري ومتحقق منه أمنياً)
    """
    product = get_object_or_404(Product, pk=pk, available=True)

    # التحقق من الكمية والمدى
    try:
        qty = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, min(qty, 20))

    _cart_add(request, product.pk, qty)
    messages.success(request, f"تمت إضافة «{product.name}» إلى السلة ✅")

    # دعم next مع تحقق أمان الدومين
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)

    return redirect("cart_detail")


@require_http_methods(["POST"])
def remove_from_cart(request, pk: int):
    """إزالة منتج من السلة (POST فقط)."""
    _cart_remove(request, pk)
    messages.success(request, "تمت إزالة العنصر من السلة.")
    return redirect("cart_detail")


@require_http_methods(["GET"])
def cart_detail(request):
    """
    عرض محتوى السلة من الجلسة.
    السياق المعاد:
      - items: قائمة عناصر فيها {product, qty, line_total}
      - total: الإجمالي الكلي
    القالب: templates/cart/cart_detail.html
    """
    cart = _cart_get(request)
    if not cart:
        return render(request, "cart/cart_detail.html", {"items": [], "total": 0})

    ids = [int(i) for i in cart.keys() if str(i).isdigit()]
    products = Product.objects.filter(id__in=ids)

    items: List[Dict[str, Any]] = []
    total = 0
    # ضمان ترتيب ثابت اختياريًا: حسب id
    products = sorted(products, key=lambda p: p.pk)
    for p in products:
        qty = int(cart.get(str(p.pk), 0))
        line_total = (p.price or 0) * qty
        total += line_total
        items.append({"product": p, "qty": qty, "line_total": line_total})

    return render(request, "cart/cart_detail.html", {"items": items, "total": total})


# =========================
#     أدوات ربط المنتج بالكورس
# =========================
def _resolve_or_create_course_from_product(p: Product) -> Course:
    """
    يحاول إيجاد Course مناسب للمنتج:
    1) Product.course إن وجد
    2) Course بالعنوان = product.name
    3) Course بالـ slug = product.slug (إن وجد)
    4) إنشاء Course تلقائيًا من بيانات المنتج
    """
    # 1) ربط مباشر
    course = getattr(p, "course", None)
    if course:
        return course

    # 2) بالعنوان
    course = Course.objects.filter(title=p.name).first()
    if course:
        return course

    # 3) بالـ slug (لو عند المنتج)
    p_slug = getattr(p, "slug", None)
    if p_slug:
        course = Course.objects.filter(slug=p_slug).first()
        if course:
            return course

    # 4) إنشاء تلقائي
    auto_slug = (p_slug or f"p{p.pk}-{slugify(p.name)[:40]}") or f"p{p.pk}"
    course = Course.objects.create(
        title=p.name,
        slug=auto_slug,
        is_active=True,
        duration_days=30,                        # مدة افتراضية
        teams_link=getattr(p, "teams_link", "") or "",
    )
    return course


# =========================
#          Checkout
# =========================
@require_http_methods(["GET", "POST"])
@login_required
def checkout(request):
    """
    صفحة تأكيد الطلب/الحجز (بدون بوابة دفع الآن).
    - GET: تعرض ملخص السلة.
    - POST: تؤكّد وتحوّل عناصر السلة إلى Enrollments للطالب (مع إنشاء Course تلقائي عند الحاجة)، ثم تفرغ السلة.
    """
    cart = _cart_get(request)
    if not cart:
        messages.error(request, "سلتك فارغة. أضيفي عناصر أولًا.")
        return redirect("cart_detail")

    ids = [int(i) for i in cart.keys() if str(i).isdigit()]
    products = Product.objects.filter(id__in=ids).order_by("id")

    items: List[Dict[str, Any]] = []
    total = 0
    for p in products:
        qty = int(cart.get(str(p.pk), 0))
        line_total = (p.price or 0) * qty
        total += line_total
        items.append({"product": p, "qty": qty, "line_total": line_total})

    if request.method == "POST":
        # في هذا الإصدار: لا بوابة دفع — نفعّل التسجيلات مباشرة
        student, _ = Student.objects.get_or_create(user=request.user)
        created_any = False

        for it in items:
            p = it["product"]

            # ✅ احصل/أنشئ Course مناسب لهذا المنتج
            course = _resolve_or_create_course_from_product(p)

            # إنشاء/تفعيل التسجيل
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    "status": "active",
                    "joined_at": timezone.now(),
                    "starts_at": timezone.now(),
                    "ends_at": timezone.now() + timedelta(days=getattr(course, "duration_days", 30) or 30),
                    "teams_link": getattr(course, "teams_link", "") or "",
                },
            )

            if not created:
                # تحديث تسجيل سابق ليصبح نشطًا ضمن نافذة زمنية صالحة
                if enrollment.status != "active":
                    enrollment.status = "active"
                if not enrollment.starts_at:
                    enrollment.starts_at = timezone.now()
                if not enrollment.ends_at:
                    enrollment.ends_at = enrollment.starts_at + timedelta(days=getattr(course, "duration_days", 30) or 30)
                if not enrollment.teams_link:
                    enrollment.teams_link = getattr(course, "teams_link", "") or ""
                enrollment.save()
            else:
                created_any = True

        # ✅ إفراغ السلة وإعلام المستخدم
        request.session["cart"] = {}
        request.session.modified = True

        if created_any:
            messages.success(request, "تم تأكيد طلبك وتفعيل الدورات في لوحة الطالب ✅")
        else:
            messages.info(request, "تم التأكيد. لا توجد دورات جديدة لتفعيلها.")

        return redirect("students:dashboard")

    # GET → عرض صفحة التأكيد
    return render(request, "cart/checkout.html", {"items": items, "total": total})


# =========================
#   حجز سريع من صفحة الدورة
# =========================
@require_http_methods(["POST"])
def quick_book(request, pk: int):
    """
    حجز مباشر من صفحة المنتج دون فتح نموذج الحجز الطويل.
    يرسل بريدًا تنبيهيًا (لا يوقف العملية لو فشل)، ثم يرجع لصفحة المنتج.
    """
    product = get_object_or_404(Product, pk=pk, available=True)

    user_info = "-"
    if request.user.is_authenticated:
        user_info = f"username={request.user.username}, email={getattr(request.user, 'email', '-') or '-'}"
    ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR") or "-"

    subject_line = f"حجز سريع - {product.name}"
    body = (
        "تم استلام حجز سريع للدورة:\n"
        f"- المنتج: {product.name}\n"
        f"- معرف المنتج: {product.pk}\n"
        f"- المستخدم: {user_info}\n"
        f"- IP: {ip}\n"
        f"- المسار: {request.build_absolute_uri()}\n"
    )

    try:
        send_mail(subject_line, body, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=True)
        messages.success(request, "تم الحجز بنجاح! سنتواصل معك لتأكيد التفاصيل.")
    except Exception:
        messages.success(request, "تم الحجز بنجاح! (تعذّر إرسال بريد التنبيه الآن)")

    return redirect("product_detail", pk=product.pk)


# =========================
#  صفحة نموذج الحجز العام
# =========================
@require_http_methods(["GET", "POST"])
def booking_page(request):
    """
    نموذج حجز عام غير مرتبط بأي منتج.
    - GET: يعرض النموذج فقط.
    - POST: يتحقق من الحقول، يرسل بريدًا تنبيهيًا (اختياري)،
            وإن وُجد product_id ضمن POST يضيفه للسلة،
            ثم يحوّل دائمًا إلى صفحة السلة cart_detail.
    """
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        stage = (request.POST.get("stage") or "").strip()
        subjects: List[str] = request.POST.getlist("subjects")

        # ✅ تحقّق أساسي
        errors: List[str] = []
        if len(name) < 2:
            errors.append("الاسم قصير جدًا.")
        if not PHONE_RX.match(phone):
            errors.append("رقم الجوال غير صالح. أدخل 8–15 رقمًا مع + اختياري.")
        if not stage:
            errors.append("المرحلة الدراسية مطلوبة.")

        if errors:
            for e in errors:
                messages.error(request, e, extra_tags="booking")
            ctx: Dict[str, Any] = {
                "old": {"name": name, "phone": phone, "stage": stage, "subjects": subjects},
            }
            return render(request, "store/booking.html", ctx)

        # (اختياري) إضافة منتج للسلة إذا أُرسل product_id ضمن POST
        posted_product_id: Optional[str] = request.POST.get("product_id")
        if posted_product_id:
            try:
                product = get_object_or_404(Product, pk=posted_product_id, available=True)
                _cart_add(request, product.pk, qty=1)
                messages.success(request, "تمت إضافة الدورة إلى السلة ✅", extra_tags="booking")
            except Exception:
                # نتجاهل أي خطأ هنا حتى لا نفشل الطلب كاملًا
                pass

        # (اختياري) بريد تنبيهي — لا يعطل العملية
        try:
            subj = "طلب حجز جديد (بدون تحديد منتج)"
            body = (
                f"الاسم: {name}\n"
                f"الجوال: {phone}\n"
                f"المرحلة: {stage}\n"
                f"المواد: {', '.join(subjects) if subjects else '-'}\n"
            )
            send_mail(subj, body, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=True)
        except Exception:
            pass

        # ✅ التحويل دائمًا إلى صفحة السلة
        return redirect("cart_detail")

    # GET
    return render(request, "store/booking.html", {})


# =========================
#      لوحة المعلم
# =========================
@login_required
@require_http_methods(["GET"])
def teacher_dashboard(request):
    if getattr(request.user, "role", None) != "teacher":
        messages.error(request, "غير مصرح بالوصول إلى لوحة المعلم.")
        return redirect("product_list")
    return render(request, "store/teacher_dashboard.html")
