from django.urls import path
from .views import (
    home,
    header,
    footer,
    register_view,
    login_view,
    logout_view,     # ✅ أضف هذا
    contact,
    privacy_view,
    terms_view,
    book_lesson,
)

urlpatterns = [
    path('', home, name='home'),
    path('header/', header, name='header'),
    path('footer/', footer, name='footer'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),  # ✅ تسجيل الخروج
    path('contact/', contact, name='contact'),
    path('privacy/', privacy_view, name='privacy'),
    path('terms/', terms_view, name='terms'),
    path('book/', book_lesson, name='book_lesson'),
]
