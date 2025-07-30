from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),  # عرض كل المنتجات
    path('<int:pk>/', views.product_detail, name='product_detail'),  # تفاصيل منتج معيّن
]
