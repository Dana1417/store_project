# store_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# =========================
# تخصيص واجهة لوحة التحكم
# =========================
admin.site.site_header = "لوحة إدارة المشروع"
admin.site.site_title = "إدارة المشروع"
admin.site.index_title = "مرحبًا بك في لوحة الإدارة"

# =========================
# روابط المشروع
# =========================
urlpatterns = [
    # لوحة التحكم
    path("admin/", admin.site.urls),
    path("adminpanel/", include(("adminpanel.urls", "adminpanel"), namespace="adminpanel")),

    # الصفحات العامة
    path("", include("core.urls")),
    path("", include("store.urls")),

    # الطلبات والسلة
    path("orders/", include("orders.urls")),
    path("cart/", include("cart.urls")),

    # الطالب
    path("student/", include(("students.urls", "students"), namespace="students")),

    # المعلّم (ندعم teacher و teachers معاً)
    path("teachers/", include(("teachers.urls", "teachers"), namespace="teachers")),
    path("teacher/", include(("teachers.urls", "teachers_alt"), namespace="teachers_alt")),

    # =========================
    # تسجيل الدخول / الخروج
    # =========================
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="core/login.html"),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(template_name="core/logout.html"),
        name="logout",
    ),

    # =========================
    # استرجاع / إعادة تعيين كلمة المرور (قوالب من registration/)
    # =========================
    path(
        "accounts/password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "accounts/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]

# =========================
# رفع الوسائط أثناء التطوير
# =========================
if settings.DEBUG:
    media_url = getattr(settings, "MEDIA_URL", None)
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if media_url and media_root:
        urlpatterns += static(media_url, document_root=media_root)
