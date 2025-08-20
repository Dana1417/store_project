# store/views.py
from __future__ import annotations
from typing import Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .models import Product
from orders.models import Order
from students.models import Student, Enrollment


# =========================
#     أدوات السلة (Session)
# =========================
def _cart_get(request) -> Dict[str, int]:
    """إرجاع محتوى السلة من السيشن."""
    return request.session.get("cart", {})


def _cart_save(request, cart: Dict[str, int]) -> None:
    """حفظ السلة في السيشن."""
    request.session["cart"] = cart
    request.session.modified = True


# =========================
#       قائمة المنتجات
# =========================
@require_http_methods(["GET"])
def product_list(request):
    products = Product.objects.filter(available=True).order_by("-id")
    return render(request, "store/product_list.html", {"products": products})


# =========================
#     تفاصيل منتج
# =========================
@require_http_methods(["GET"])
def product_detail(request, pk: int):
    product = get_object_or_404(Product, pk=pk, available=True)
    return render(request, "store/product_detail.html", {"product": product})


# =========================
#    إضافة للسلة
# =========================
@login_required
@require_http_methods(["POST"])
def add_to_cart(request, pk: int):
    product = get_object_or_404(Product, pk=pk, available=True)
    cart = _cart_get(request)
    cart[str(pk)] = cart.get(str(pk), 0) + 1
    _cart_save(request, cart)
    messages.success(request, f"تمت إضافة {product.name} إلى السلة.")
    return redirect("store:cart_detail")


# =========================
#   إزالة من السلة
# =========================
@login_required
@require_http_methods(["POST"])
def remove_from_cart(request, pk: int):
    cart = _cart_get(request)
    if str(pk) in cart:
        del cart[str(pk)]
        _cart_save(request, cart)
        messages.info(request, "تمت إزالة المنتج من السلة.")
    return redirect("store:cart_detail")


# =========================
#   تفاصيل السلة
# =========================
@login_required
@require_http_methods(["GET"])
def cart_detail(request):
    cart = _cart_get(request)
    products = Product.objects.filter(id__in=cart.keys())

    items, total = [], 0
    for product in products:
        qty = cart.get(str(product.id), 0)
        subtotal = product.price * qty
        items.append({
            "product": product,
            "quantity": qty,
            "subtotal": subtotal,
        })
        total += subtotal

    return render(request, "store/cart_detail.html", {"items": items, "total": total})


# =========================
#   حجز سريع (زر احجز الآن)
# =========================
@login_required
@require_http_methods(["POST", "GET"])
def quick_book(request, pk: int):
    product = get_object_or_404(Product, pk=pk, available=True)
    # تعيين السلة بمنتج واحد فقط
    cart = {str(product.id): 1}
    _cart_save(request, cart)
    messages.success(request, f"✅ تم حجز {product.name} بنجاح")
    return redirect("store:checkout")


# =========================
#   صفحة الدفع (Checkout)
# =========================
@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def checkout(request):
    cart = _cart_get(request)
    if not cart:
        messages.error(request, "🚫 السلة فارغة.")
        return redirect("store:product_list")

    products = Product.objects.filter(id__in=cart.keys())
    total = sum(product.price * cart[str(product.id)] for product in products)

    if request.method == "POST":
        student, _ = Student.objects.get_or_create(user=request.user)

        for product in products:
            qty = cart[str(product.id)]
            # إنشاء طلب لكل منتج (حسب تصميم Order الحالي)
            order = Order.objects.create(
                user=request.user,
                product=product,
                quantity=qty,
                status=Order.STATUS_CONFIRMED,
            )
            order.total_price = product.price * qty
            order.save()

            # إذا المنتج مربوط بدورة → نسجل الطالب فيها
            if product.course:
                Enrollment.objects.get_or_create(
                    student=student,
                    course=product.course,
                )

        # إفراغ السلة
        request.session["cart"] = {}
        request.session.modified = True

        messages.success(request, "🎉 تم تنفيذ الطلب وتفعيل الدورات بنجاح")
        return redirect("students:dashboard")

    return render(request, "store/checkout.html", {"products": products, "total": total})


# =========================
#   صفحة الحجز العام
# =========================
@require_http_methods(["GET", "POST"])
def booking_page(request):
    """
    نموذج الحجز العام:
    - إذا جاء product_id من GET → تعبئة المنتج.
    - يسمح بإرسال معلومات إضافية (اسم/جوال/مرحلة).
    """
    products = Product.objects.filter(available=True)

    # المنتج المختار من زر "احجز الآن"
    product_id = request.GET.get("product_id")
    selected_product = None
    if product_id:
        selected_product = Product.objects.filter(id=product_id, available=True).first()

    # تعبئة بيانات سابقة
    old = {
        "name": request.POST.get("name", ""),
        "phone": request.POST.get("phone", ""),
        "stage": request.POST.get("stage", ""),
        "product_id": request.POST.get("product_id", product_id or ""),
        "subjects": request.POST.getlist("subjects"),
    }

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        stage = request.POST.get("stage")
        messages.success(request, f"✅ شكراً {name}، تم استلام طلبك وسنتواصل معك قريباً.")
        return redirect("store:booking")

    return render(request, "store/booking.html", {
        "products": products,
        "selected_product": selected_product,
        "old": old,
    })
