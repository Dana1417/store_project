from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ✅ لوحة التحكم
    path('admin/', admin.site.urls),

    # ✅ ربط التطبيقات
    path('', include('core.urls')),          # الصفحات العامة: الرئيسية، تواصل معنا، التسجيل، إلخ
    path('', include('store.urls')),         # المنتجات، تفاصيل منتج، الحجز، لوحة الطالب والمعلم
    path('orders/', include('orders.urls')), # الطلبات
    path('cart/', include('cart.urls')),     # سلة المشتريات
]

# ✅ عرض ملفات الوسائط media أثناء التطوير فقط
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ✅ عرض ملفات static بعد `collectstatic` (أثناء التطوير فقط)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
