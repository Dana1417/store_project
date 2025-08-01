from django.urls import path
from .views import (
    home,
    header,
    footer,
    register_view,
    login_view,
    contact,
    privacy_view,
    terms_view,
    book_lesson,   # ✅ مسار معالجة نموذج الحجز
)

urlpatterns = [
    path('', home, name='home'),                          # الصفحة الرئيسية
    path('header/', header, name='header'),               # الهيدر
    path('footer/', footer, name='footer'),               # الفوتر
    path('register/', register_view, name='register'),    # إنشاء حساب
    path('login/', login_view, name='login'),             # تسجيل الدخول
    path('contact/', contact, name='contact'),            # تواصل معنا
    path('privacy/', privacy_view, name='privacy'),       # سياسة الخصوصية
    path('terms/', terms_view, name='terms'),             # الشروط والأحكام
    path('book/', book_lesson, name='book_lesson'),       # ✅ معالجة نموذج "احجز الآن"
]
