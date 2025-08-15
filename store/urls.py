from django.urls import path
from . import views

urlpatterns = [
    # ✅ قائمة المنتجات
    path("products/", views.product_list, name="product_list"),

    # ✅ تفاصيل منتج معيّن
    path("products/<int:pk>/", views.product_detail, name="product_detail"),

    # ✅ نموذج الحجز (العام)
    path("booking/", views.booking_page, name="booking"),

    # ✅ حجز سريع (POST فقط) من صفحة المنتج
    path("book/<int:pk>/quick/", views.quick_book, name="quick_book"),

    # ✅ السلة (Session)
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),             # POST
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),# POST

    # ✅ التأكيد/الدفع (بدون بوابة دفع حالياً)
    path("checkout/", views.checkout, name="checkout"),

    # ✅ لوحة المعلّم
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
]
