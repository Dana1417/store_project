from django.urls import path
from . import views

urlpatterns = [
    # ✅ عرض جميع المنتجات
    path('products/', views.product_list, name='product_list'),

    # ✅ عرض تفاصيل منتج معيّن عبر الـ ID
    path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # ✅ نموذج حجز درس
    path('booking/', views.booking_page, name='booking_page'),

    # ✅ لوحة الطالب (بعد تسجيل الدخول والتحقق من الدور)
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

    # ✅ لوحة المعلم (بعد تسجيل الدخول والتحقق من الدور)
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
]
