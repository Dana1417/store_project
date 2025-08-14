from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    # ✅ عرض جميع المنتجات
    path("products/", views.product_list, name="product_list"),

    # ✅ عرض تفاصيل منتج معيّن عبر الـ ID
    path("products/<int:pk>/", views.product_detail, name="product_detail"),

    # ✅ نموذج حجز درس
    path("booking/", views.booking_page, name="booking_page"),

    # ✅ لوحة المعلم (إن كنتِ تستخدمينها)
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
]
