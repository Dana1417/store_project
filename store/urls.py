from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    # المنتجات
    path("products/", views.product_list, name="product_list"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),

    # الحجز
    path("booking/", views.booking_page, name="booking"),
    path("book/<int:pk>/quick/", views.quick_book, name="quick_book"),

    # السلة
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),

    # الدفع
    path("checkout/", views.checkout, name="checkout"),
]
