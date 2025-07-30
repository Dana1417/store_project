from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from store.models import Product  # ← استيراد المنتجات من قاعدة البيانات

# ✅ الصفحة الرئيسية
def home(request):
    products = Product.objects.filter(available=True).order_by('-created_at')
    return render(request, 'home.html', {'products': products})

# ✅ الهيدر
def header(request):
    return render(request, 'header.html')

# ✅ الفوتر
def footer(request):
    return render(request, 'footer.html')

# ✅ صفحة إنشاء حساب
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
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
