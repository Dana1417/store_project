from django.urls import path
from .views import home, header, footer, register_view, login_view

urlpatterns = [
    path('', home, name='home'),
    path('header/', header, name='header'),
    path('footer/', footer, name='footer'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
]
