# store_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# =========================
#   تخصيص واجهة لوحة التحكم
# =========================
admin.site.site_header = "لوحة إدارة المشروع"
admin.site.site_title = "إدارة المشروع"
admin.site.index_title = "مرحبًا بك في لوحة الإدارة"

# =========================
#         روابط المشروع
# =========================
urlpatterns = [
    # لوحة التحكم الافتراضية Django
    path("admin/", admin.site.urls),

    # لوحة المشرف (Admin Panel المخصّصة)
    path("adminpanel/", include(("adminpanel.urls", "adminpanel"), namespace="adminpanel")),

    # الصفحات الرئيسية (core + المتجر)
    path("", include("core.urls")),       # الرئيسية، تواصل معنا، إلخ
    path("", include("store.urls")),      # المنتجات وتفاصيل المنتج

    # الطلبات والسلة
    path("orders/", include("orders.urls")),
    path("cart/", include("cart.urls")),

    # لوحة الطالب
    path("student/", include(("students.urls", "students"), namespace="students")),

    # لوحة المعلّم
    path("teachers/", include(("teachers.urls", "teachers"), namespace="teachers")),
]

# =========================
#   خدمة ملفات MEDIA (محليًا)
# =========================
if settings.DEBUG:
    media_url = getattr(settings, "MEDIA_URL", None)
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if media_url and media_root:
        urlpatterns += static(media_url, document_root=media_root)
