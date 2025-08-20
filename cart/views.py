from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from store.models import Product  # تأكد من المسار الصحيح لموديل المنتج

# مفاتيح وإعدادات بسيطة
CART_SESSION_KEY = "cart"
MAX_QTY_PER_ITEM = 99


def _get_cart(request) -> Dict[str, int]:
    """إحضار السلة من السيشن (قاموس: product_id كسلسلة -> quantity)."""
    return request.session.get(CART_SESSION_KEY, {})


def _save_cart(request, cart: Dict[str, int]) -> None:
    """حفظ السلة في السيشن."""
    request.session[CART_SESSION_KEY] = cart


def _safe_redirect_next(request, fallback_name: str = "cart_detail"):
    """
    إعادة توجيه آمنة لبرتاميتر next إن كان من نفس الأصل؛ غير ذلك نرجع للـ cart_detail.
    """
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return redirect(fallback_name)


@require_POST
def add_to_cart(request, product_id: int):
    """
    إضافة منتج واحد للسلة:
    - يتحقق من وجود المنتج.
    - يمنع تجاوز حد الكمية MAX_QTY_PER_ITEM.
    - يدعم حقول stock اختياريًا (إن وجدت).
    """
    product = get_object_or_404(Product, pk=product_id)
    cart = _get_cart(request)
    key = str(product_id)

    current_qty = int(cart.get(key, 0))
    new_qty = min(current_qty + 1, MAX_QTY_PER_ITEM)

    # تحقق اختياري من المخزون إن كان الحقل موجودًا
    if hasattr(product, "stock") and product.stock is not None:
        if new_qty > int(product.stock):
            messages.warning(request, "الكمية المطلوبة تتجاوز المخزون المتاح.")
            return _safe_redirect_next(request)

    cart[key] = new_qty
    _save_cart(request, cart)
    messages.success(request, f"تمت إضافة «{product.name}» إلى السلة.")

    return _safe_redirect_next(request)


@require_POST
def remove_from_cart(request, product_id: int):
    """
    إزالة منتج من السلة بالكامل.
    """
    cart = _get_cart(request)
    key = str(product_id)
    if key in cart:
        del cart[key]
        _save_cart(request, cart)
        messages.success(request, "تمت إزالة المنتج من السلة.")
    else:
        messages.info(request, "المنتج غير موجود في السلة.")

    return _safe_redirect_next(request)


def cart_detail(request):
    """
    عرض تفاصيل السلة مع حساب الإجمالي.
    نبني مصفوفة cart_items: [{product, quantity, unit_price, subtotal}, ...]
    """
    cart = _get_cart(request)
    cart_items: List[dict] = []
    total = Decimal("0.00")

    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
            quantity = int(qty)
        except (TypeError, ValueError):
            # تجاهل المدخلات الفاسدة
            continue

        product = get_object_or_404(Product, pk=pid)
        unit_price = product.price if hasattr(product, "price") and product.price is not None else Decimal("0.00")

        # تأكد أن السعر Decimal
        if not isinstance(unit_price, Decimal):
            unit_price = Decimal(str(unit_price))

        subtotal = (unit_price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return render(request, "cart/cart_detail.html", {
        "cart_items": cart_items,
        "cart_total": total,
    })
