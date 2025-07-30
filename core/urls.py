# /Users/hlm../store_project/core/urls.py

from django.urls import path
from .views import (
    home,
    header,
    footer,
    register_view,
    login_view,
    contact,
    privacy_view,     # ✅ تمت إضافتها
    terms_view        # ✅ تمت إضافتها
)

urlpatterns = [
    path('', home, name='home'),                     # الرئيسية
    path('header/', header, name='header'),          # الهيدر
    path('footer/', footer, name='footer'),          # الفوتر
    path('register/', register_view, name='register'),  # إنشاء حساب
    path('login/', login_view, name='login'),           # تسجيل دخول
    path('contact/', contact, name='contact'),          # تواصل معنا

    # ✅ صفحات جديدة
    path('privacy/', privacy_view, name='privacy'),     # سياسة الخصوصية
    path('terms/', terms_view, name='terms'),           # الشروط والأحكام
]
