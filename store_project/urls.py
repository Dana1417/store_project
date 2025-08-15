# store_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # لوحة التحكم
    path("admin/", admin.site.urls),

    # تطبيقات المشروع الرئيسية
    path("", include("core.urls")),           # الرئيسية، تواصل معنا، ...الخ
    path("", include("store.urls")),          # المنتجات، تفاصيل منتج، الحجز، ...الخ
    path("orders/", include("orders.urls")),  # الطلبات
    path("cart/", include("cart.urls")),      # السلة

    # ✅ لوحة الطالب (namespace)
    path(
        "student/",
        include(("students.urls", "students"), namespace="students")
    ),

    # ✅ لوحة المعلّم (namespace)
    path(
        "teachers/",
        include(("teachers.urls", "teachers"), namespace="teachers")
    ),
]

# عرض ملفات الوسائط أثناء التطوير
if settings.DEBUG:
    # وسائط (Cloudinary غالبًا يُرجع روابط كاملة؛ السطر التالي مفيد للوسائط المحلية إن وُجدت)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # (اختياري) خدمة الملفات الثابتة محليًا إن رغبتِ
    # from django.conf import settings as dj_settings
    # urlpatterns += static(dj_settings.STATIC_URL, document_root=dj_settings.STATIC_ROOT)
