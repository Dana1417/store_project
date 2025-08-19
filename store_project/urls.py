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
    path("", include("core.urls")),            # الصفحة الرئيسية وما شابه
    path("", include("store.urls")),           # المنتجات وتفاصيل المنتج

    path("orders/", include("orders.urls")),   # الطلبات (Checkout/Pay/Success)
    path("cart/", include("cart.urls")),       # السلة

    # لوحة الطالب (namespace = students)
    path("student/", include(("students.urls", "students"), namespace="students")),

    # لوحة المعلّم (namespace = teachers)
    path("teachers/", include(("teachers.urls", "teachers"), namespace="teachers")),
]

# أثناء التطوير فقط: خدمة MEDIA إن كانت معرفة محليًا
if settings.DEBUG:
    media_url = getattr(settings, "MEDIA_URL", None)
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if media_url and media_root:
        urlpatterns += static(media_url, document_root=media_root)
