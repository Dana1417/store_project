from django.urls import path
from .views import (
    home,
    header,
    footer,
    register_view,
    login_view,
    logout_view,
    contact,
    privacy_view,
    terms_view,
    book_lesson,
)

urlpatterns = [
    # ✅ الصفحة الرئيسية
    path('', home, name='home'),

    # ✅ تضمين الهيدر والفوتر (إذا تستخدم التضمين اليدوي)
    path('header/', header, name='header'),
    path('footer/', footer, name='footer'),

    # ✅ الحسابات
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # ✅ الصفحات العامة
    path('contact/', contact, name='contact'),
    path('privacy/', privacy_view, name='privacy'),
    path('terms/', terms_view, name='terms'),

    # ✅ صفحة الحجز
    path('book/', book_lesson, name='book_lesson'),
]
