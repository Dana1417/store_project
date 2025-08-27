# store_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "لوحة إدارة المشروع"
admin.site.site_title = "إدارة المشروع"
admin.site.index_title = "مرحبًا بك في لوحة الإدارة"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("adminpanel/", include(("adminpanel.urls", "adminpanel"), namespace="adminpanel")),

    path("", include("core.urls")),
    path("", include("store.urls")),

    path("orders/", include("orders.urls")),
    path("cart/", include("cart.urls")),

    path("student/", include(("students.urls", "students"), namespace="students")),
    path("teachers/", include(("teachers.urls", "teachers"), namespace="teachers")),

    # روابط تسجيل الدخول وكلمة المرور
    path("accounts/", include("django.contrib.auth.urls")),
]

if settings.DEBUG:
    media_url = getattr(settings, "MEDIA_URL", None)
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if media_url and media_root:
        urlpatterns += static(media_url, document_root=media_root)
