from django.contrib import admin
from django.urls import path, include  # ← ضروري لربط التطبيقات

urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ ربط التطبيقات الثلاثة
    path('', include('core.urls')),         # التطبيق الرئيسي (الرئيسية، من نحن، تواصل معنا)
    path('store/', include('store.urls')),  # المنتجات والتصنيفات
    path('orders/', include('orders.urls')), # الطلبات والمدفوعات
]
