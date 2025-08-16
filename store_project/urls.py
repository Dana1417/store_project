# store_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# تخصيص واجهة لوحة التحكم (اختياري)
admin.site.site_header = "لوحة إدارة المشروع"
admin.site.site_title = "إدارة المشروع"
admin.site.index_title = "مرحبًا بك في لوحة الإدارة"

urlpatterns = [
    # لوحة التحكم
    path("admin/", admin.site.urls),

    # تطبيقات المشروع الرئيسية
    path("", include("core.urls")),             # الرئيسية، تواصل معنا، ...الخ
    path("", include("store.urls")),            # المنتجات، تفاصيل المنتج، الحجز، ...الخ
    path("orders/", include("orders.urls")),    # الطلبات
    path("cart/", include("cart.urls")),        # السلة

    # ✅ لوحة الطالب (namespace)
    path(
        "student/",
        include(("students.urls", "students"), namespace="students"),
    ),

    # ✅ لوحة المعلّم (namespace)
    path(
        "teachers/",
        include(("teachers.urls", "teachers"), namespace="teachers"),
    ),
]

# عرض ملفات الوسائط والملفات الثابتة أثناء التطوير فقط
if settings.DEBUG:
    # وسائط المستخدم (MEDIA)
    if getattr(settings, "MEDIA_URL", None) and getattr(settings, "MEDIA_ROOT", None):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # (اختياري) الملفات الثابتة لو رغبتِ بعرضها عبر Django محليًا
    # ملاحظة: في الإنتاج نستخدم WhiteNoise/Cloud Storage
    if getattr(settings, "STATIC_URL", None) and getattr(settings, "STATIC_ROOT", None):
        # ألغِ التعليق التالي إذا أردتِ خدمة static من STATIC_ROOT أثناء التطوير
        # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        pass
