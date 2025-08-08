from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ ربط التطبيقات
    path('', include('core.urls')),          # الصفحة الرئيسية وتواصل معنا وغيرها
    path('', include('store.urls')),         # المنتجات على المسار الجذري
    path('orders/', include('orders.urls')), # الطلبات
    path('cart/', include('cart.urls')),     # 🛒 سلة المشتريات
]

# ✅ عرض ملفات media أثناء التطوير فقط
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ✅ عرض staticfiles مباشرة عند استخدام collectstatic (اختياري)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
