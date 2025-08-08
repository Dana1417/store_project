from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product_list'),                # ✅ صفحة عرض جميع المنتجات
    path('products/<int:pk>/', views.product_detail, name='product_detail'),   # ✅ صفحة تفاصيل منتج معيّن
    
    path('booking/', views.booking_page, name='booking_page'),                 # ✅ صفحة الحجز
]
