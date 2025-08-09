from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Student

# ✅ عرض جميع المنتجات المتاحة
def product_list(request):
    products = Product.objects.filter(available=True).order_by('-created_at')
    return render(request, 'store/product_list.html', {
        'products': products
    })

# ✅ عرض تفاصيل منتج معيّن باستخدام الـ ID
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    return render(request, 'store/product_detail.html', {
        'product': product
    })

# ✅ صفحة نموذج الحجز
def booking_page(request):
    return render(request, 'store/booking_form.html')

# ✅ لوحة الطالب (تظهر فقط إذا كان المستخدم طالبًا)
@login_required
def student_dashboard(request):
    if getattr(request.user, 'role', None) != 'student':
        return redirect('home')  # 🔒 منع الوصول لغير الطلاب

    student = get_object_or_404(Student, user=request.user)
    return render(request, 'store/student_dashboard.html', {
        'student': student
    })

# ✅ لوحة المعلم (تظهر فقط إذا كان المستخدم معلمًا)
@login_required
def teacher_dashboard(request):
    if getattr(request.user, 'role', None) != 'teacher':
        return redirect('home')  # 🔒 منع الوصول لغير المعلمين

    return render(request, 'store/teacher_dashboard.html')
