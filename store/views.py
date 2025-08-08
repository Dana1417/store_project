from django.shortcuts import render, get_object_or_404
from .models import Product

# ✅ عرض جميع المنتجات المتاحة
def product_list(request):
    products = Product.objects.filter(available=True).order_by('-created_at')
    return render(request, 'store/product_list.html', {
        'products': products
    })

# ✅ عرض تفاصيل منتج محدد باستخدام الـ PK
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    return render(request, 'store/product_detail.html', {
        'product': product
    })

# ✅ عرض صفحة نموذج الحجز
def booking_page(request):
    return render(request, 'store/booking.html')
