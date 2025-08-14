from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # لوحة التحكم
    path('admin/', admin.site.urls),

    # تطبيقاتك الأخرى
    path('', include('core.urls')),           # الرئيسية، تواصل معنا، التسجيل، ...الخ
    path('', include('store.urls')),          # المنتجات، تفاصيل منتج، الحجز، ...الخ
    path('orders/', include('orders.urls')),  # الطلبات
    path('cart/', include('cart.urls')),      # السلة

    # ✅ ربط لوحة الطالب من تطبيق students
    path('student/', include(('students.urls', 'students'), namespace='students')),
]

# عرض ملفات الوسائط أثناء التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
