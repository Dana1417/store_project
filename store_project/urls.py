from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ ربط التطبيقات
    path('', include('core.urls')),         # الرئيسية، تواصل معنا، الخ...
    path('store/', include('store.urls')),  # المنتجات
    path('orders/', include('orders.urls')), # الطلبات
]

# ✅ عرض ملفات media أثناء التطوير فقط
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ✅ عرض staticfiles مباشرة عند استخدام collectstatic (اختياري)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
