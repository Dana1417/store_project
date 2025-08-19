# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("success/", views.checkout_success, name="checkout_success"),
    path("pay/<int:order_id>/", views.pay_now, name="pay_now"),          # صفحة دفع تجريبية
    path("webhook/", views.payment_webhook, name="payment_webhook"),     # ويبهوك اختياري
]
