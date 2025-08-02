from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

from .forms import CustomUserCreationForm
from store.models import Product


# ✅ الصفحة الرئيسية - عرض المنتجات المتاحة
def home(request):
    products = Product.objects.filter(available=True).order_by('-created_at')
    return render(request, 'home.html', {'products': products})


# ✅ عرض الهيدر
def header(request):
    return render(request, 'header.html')


# ✅ عرض الفوتر
def footer(request):
    return render(request, 'footer.html')


# ✅ صفحة إنشاء حساب جديد
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "🎉 تم إنشاء الحساب بنجاح، مرحبًا بك!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})


# ✅ صفحة تسجيل الدخول
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data.get('username'),
                password=form.cleaned_data.get('password')
            )
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


# ✅ صفحة تواصل معنا
def contact(request):
    return render(request, 'core/contact.html')


# ✅ صفحة سياسة الخصوصية
def privacy_view(request):
    return render(request, 'core/privacy.html')


# ✅ صفحة الشروط والأحكام
def terms_view(request):
    return render(request, 'core/terms.html')


# ✅ صفحة ومعالجة نموذج الحجز
def book_lesson(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        grade = request.POST.get("grade")
        subjects = request.POST.getlist("subjects")  # ← لأن المستخدم قد يختار أكثر من مادة

        # 🟠 هنا يمكنك إنشاء نموذج Django Model لحفظ هذه البيانات في قاعدة البيانات

        messages.success(request, "✅ تم إرسال طلب الحجز بنجاح! سنتواصل معك قريبًا.")
        return redirect('home')

    # ✅ إذا كانت الطلب GET → عرض صفحة نموذج الحجز
    return render(request, 'core/booking_form.html')
