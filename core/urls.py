from django.urls import path
from .views import home, header, footer, register_view, login_view, contact

urlpatterns = [
    path('', home, name='home'),                     # الرئيسية
    path('header/', header, name='header'),          # الهيدر
    path('footer/', footer, name='footer'),          # الفوتر
    path('register/', register_view, name='register'),  # إنشاء حساب
    path('login/', login_view, name='login'),           # تسجيل دخول
    path('contact/', contact, name='contact'),          # ✅ تواصل معنا
]
