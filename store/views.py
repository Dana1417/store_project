from __future__ import annotations
from typing import Dict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .models import Product, Booking
from orders.models import Order
from students.models import Student, Enrollment


# =========================
#     أدوات السلة (Session)
# =========================
def _cart_get(request) -> Dict[str, int]:
    return request.session.get("cart", {})


def _cart_save(request, cart: Dict[str, int]) -> None:
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
#   تحديث الكمية
# =========================
@login_required
@require_http_methods(["POST"])
def update_cart(request, pk: int):
    action = request.POST.get("action")
    cart = _cart_get(request)

    if str(pk) in cart:
        if action == "increase":
            cart[str(pk)] += 1
        elif action == "decrease":
            cart[str(pk)] -= 1
            if cart[str(pk)] <= 0:
                del cart[str(pk)]

    _cart_save(request, cart)
    return redirect("store:cart_detail")


# =========================
#   تفاصيل السلة
# =========================
@login_required
@require_http_methods(["GET"])
def cart_detail(request):
    cart = _cart_get(request)
    products = Product.objects.filter(id__in=cart.keys())

    items, total = [], Decimal("0.00")
    for product in products:
        qty = cart.get(str(product.id), 0)
        subtotal = product.price * qty
        items.append({
            "product": product,
            "quantity": qty,
            "subtotal": subtotal,
        })
        total += subtotal

    # ✅ حساب الضريبة والإجمالي بالـ Decimal
    tax_rate = Decimal("0.15")
    tax = (total * tax_rate).quantize(Decimal("0.01"))
    grand_total = total + tax

    return render(request, "store/cart_detail.html", {
        "items": items,
        "total": total,
        "tax": tax,
        "grand_total": grand_total,
    })


# =========================
#   حجز سريع (زر احجز الآن)
# =========================
@login_required
@require_http_methods(["POST", "GET"])
def quick_book(request, pk: int):
    product = get_object_or_404(Product, pk=pk, available=True)
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
    total = Decimal("0.00")

    for product in products:
        qty = cart[str(product.id)]
        total += product.price * qty

    tax_rate = Decimal("0.15")
    tax = (total * tax_rate).quantize(Decimal("0.01"))
    grand_total = total + tax

    if request.method == "POST":
        student, _ = Student.objects.get_or_create(user=request.user)

        for product in products:
            qty = cart[str(product.id)]
            order = Order.objects.create(
                user=request.user,
                product=product,
                quantity=qty,
                status=Order.STATUS_CONFIRMED,
                total_price=product.price * qty,
            )

            if product.course:
                Enrollment.objects.get_or_create(
                    student=student,
                    course=product.course,
                )

        request.session["cart"] = {}
        request.session.modified = True

        messages.success(request, "🎉 تم تنفيذ الطلب وتفعيل الدورات بنجاح")
        return redirect("students:dashboard")

    return render(request, "store/checkout.html", {
        "products": products,
        "total": total,
        "tax": tax,
        "grand_total": grand_total,
    })


# =========================
#   صفحة الحجز العام
# =========================
@require_http_methods(["GET", "POST"])
def booking_page(request):
    products = Product.objects.filter(available=True)

    product_id = request.GET.get("product_id")
    selected_product = None
    if product_id:
        selected_product = Product.objects.filter(id=product_id, available=True).first()

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
        subjects = ", ".join(request.POST.getlist("subjects"))
        product_id = request.POST.get("product_id")

        course = None
        if product_id:
            product = Product.objects.filter(id=product_id).first()
            if product and product.course:
                course = product.course

        Booking.objects.create(
            full_name=name,
            phone=phone,
            stage=stage,
            subjects=subjects,
            course=course,
        )

        messages.success(request, f"✅ شكراً {name}، تم استلام طلبك وسنتواصل معك قريباً.")
        return redirect("store:booking")

    return render(request, "store/booking.html", {
        "products": products,
        "selected_product": selected_product,
        "old": old,
    })
