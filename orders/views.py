# orders/views.py
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Tuple

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from store.models import Product
from .models import Order


# ===== أدوات مساعدة للسلة =====================================================

def _get_cart_dict(request) -> Dict[str, int]:
    """إرجاع قاموس السلة من الـ Session بشكل آمن."""
    cart = request.session.get("cart", {})
    return cart if isinstance(cart, dict) else {}

def _empty_cart(request) -> None:
    request.session["cart"] = {}
    request.session.modified = True

def _build_items_from_cart(cart: Dict[str, int]) -> Tuple[List[dict], Decimal]:
    """
    يحوّل قاموس السلة إلى قائمة عناصر قابلة للعرض/الحفظ.
    كل عنصر: {product, quantity, unit_price, line_total}
    """
    items: List[dict] = []
    subtotal = Decimal("0.00")
    for pid_str, qty in cart.items():
        # نتأكد من صحة الأرقام
        try:
            pid = int(pid_str)
            qty = int(qty)
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue

        product = get_object_or_404(Product, pk=pid, available=True)
        unit_price = Decimal(product.price)  # نفترض Product.price رقم عشري
        line_total = unit_price * qty
        items.append({
            "product": product,
            "quantity": qty,
            "unit_price": unit_price,
            "line_total": line_total,
        })
        subtotal += line_total
    return items, subtotal


# ===== الفيوز =================================================================

@require_http_methods(["GET", "POST"])
def checkout(request):
    """
    صفحة إتمام الشراء:
    - GET: يعرض ملخص السلة (بدون بيانات عميل، لأن الموديل الحالي لا يخزّنها).
    - POST: ينشئ طلبًا منفصلًا لكل عنصر في السلة (Order ذو منتج واحد)، يفرغ السلة، ثم يوجّه لصفحة النجاح.
    """
    cart = _get_cart_dict(request)
    if not cart:
        messages.error(request, "سلتك فارغة.")
        return redirect("cart_detail")

    items, subtotal = _build_items_from_cart(cart)

    if request.method == "POST":
        created_ids: List[int] = []
        for it in items:
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                product=it["product"],
                quantity=it["quantity"],
                unit_price=it["unit_price"],
                status=Order.STATUS_NEW,
            )
            created_ids.append(order.id)

        _empty_cart(request)
        # نخزن المعرفات في السيشن لعرضها في صفحة النجاح
        request.session["last_order_ids"] = created_ids
        request.session.modified = True

        messages.success(request, "تم إنشاء طلبك بنجاح ✅")
        return redirect("checkout_success")

    # GET
    ctx = {"items": items, "subtotal": subtotal}
    return render(request, "orders/checkout.html", ctx)


@require_http_methods(["GET"])
def checkout_success(request):
    """
    صفحة نجاح عامة تعرض أرقام الطلبات التي أنشئت للتوّ (إن وُجدت في السيشن).
    """
    order_ids: List[int] = request.session.pop("last_order_ids", [])
    request.session.modified = True
    return render(request, "orders/checkout_success.html", {"order_ids": order_ids})
