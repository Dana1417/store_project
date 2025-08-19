# orders/views.py
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Tuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from django.conf import settings
import hmac, hashlib

from store.models import Product
from .models import Order


# =========================
#        أدوات السلة
# =========================

def _get_cart_dict(request) -> Dict[str, int]:
    """إرجاع قاموس السلة من الـ Session بشكل آمن."""
    cart = request.session.get("cart", {})
    return cart if isinstance(cart, dict) else {}


def _empty_cart(request) -> None:
    """إفراغ السلة من الجلسة."""
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
        try:
            pid = int(pid_str)
            qty = int(qty)
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue

        product = get_object_or_404(Product, pk=pid, available=True)
        unit_price = Decimal(product.price)
        line_total = unit_price * qty
        items.append({
            "product": product,
            "quantity": qty,
            "unit_price": unit_price,
            "line_total": line_total,
        })
        subtotal += line_total
    return items, subtotal


# =========================
#          الفيوز
# =========================

@require_http_methods(["GET", "POST"])
def checkout(request):
    """
    صفحة إتمام الشراء:
    - GET: يعرض ملخص السلة.
    - POST: ينشئ طلبًا، يفرغ السلة، ثم يوجّه لصفحة النجاح.
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
        request.session["last_order_ids"] = created_ids
        request.session.modified = True
        messages.success(request, "تم إنشاء طلبك بنجاح ✅")
        return redirect("orders:checkout_success")

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


@require_http_methods(["GET", "POST"])
@login_required
def pay_now(request, order_id: int):
    """
    صفحة دفع تجريبية (محاكاة):
    - GET: تعرض ملخص الطلب وزر "ادفع الآن".
    - POST: تغيّر الحالة إلى paid وتشغّل signal لتفعيل الدورة، ثم تعيدك للوحة الطالب.
    """
    order = get_object_or_404(Order, pk=order_id)

    # أمان: السماح فقط لصاحب الطلب
    if order.user_id != request.user.id:
        raise Http404("لا تملك صلاحية الوصول لهذا الطلب.")

    if request.method == "POST":
        # منع حالات غير صالحة
        if order.status == Order.STATUS_CANCELED:
            messages.error(request, "لا يمكن دفع طلب ملغي.")
            return redirect("orders:checkout_success")
        if order.status == Order.STATUS_PAID:
            messages.info(request, "الطلب مدفوع مسبقًا.")
            return redirect("students:dashboard")

        # محاكاة الدفع: غيّر الحالة إلى paid
        order.status = Order.STATUS_PAID
        order.save(update_fields=["status"])
        messages.success(request, "تم الدفع بنجاح ✅ وتم تفعيل دورتك.")
        return redirect("students:dashboard")

    return render(request, "orders/pay_now.html", {"order": order})


# ========= Webhook اختياري (محاكاة دفع خارجي) =========

@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    """
    محاكاة ويبهوك حقيقي بتوقيع HMAC:
    - Body: form-encoded يحتوي (order_id, status=paid)
    - Header: X-PAY-SIGNature = hmac_sha256(body, PAYMENT_WEBHOOK_SECRET)
    """
    secret = (getattr(settings, "PAYMENT_WEBHOOK_SECRET", "dev-secret") or "dev-secret").encode()

    provided_sig = request.headers.get("X-PAY-SIGNature", "") or request.META.get("HTTP_X_PAY_SIGNATURE", "")
    body = request.body or b""
    expected_sig = hmac.new(secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(provided_sig, expected_sig):
        return HttpResponse("bad signature", status=400)

    order_id = request.POST.get("order_id")
    status = request.POST.get("status")
    if not (order_id and status == "paid"):
        return HttpResponse("bad payload", status=400)

    order = Order.objects.filter(pk=order_id).first()
    if not order:
        return HttpResponse("order not found", status=404)

    if order.status != Order.STATUS_PAID:
        order.status = Order.STATUS_PAID
        order.save(update_fields=["status"])  # 🔔 يشغّل signal لتفعيل الدورة

    return HttpResponse("ok", status=200)
