from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product  # ✅ أزلنا Student لأنه في تطبيق students

# ✅ عرض جميع المنتجات المتاحة
def product_list(request):
    products = Product.objects.filter(available=True).order_by('-created_at')
    return render(request, 'store/product_list.html', {'products': products})

# ✅ عرض تفاصيل منتج معيّن باستخدام الـ ID
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    return render(request, 'store/product_detail.html', {'product': product})

# ✅ صفحة نموذج الحجز
def booking_page(request):
    return render(request, 'store/booking_form.html')

# ❌ (أُلغي هنا) لوحة الطالب أصبحت داخل تطبيق students
#     المسار: /student/  أو /student/dashboard/
#     استخدمي في القوالب:
#     {% url 'students:dashboard' %}

# ✅ لوحة المعلم (تظهر فقط إذا كان المستخدم معلمًا)
@login_required
def teacher_dashboard(request):
    if getattr(request.user, 'role', None) != 'teacher':
        messages.error(request, "غير مصرح بالوصول إلى لوحة المعلم.")
        return redirect('home')  # 🔒 منع الوصول لغير المعلمين
    return render(request, 'store/teacher_dashboard.html')
