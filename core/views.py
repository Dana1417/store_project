from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

from .forms import CustomUserCreationForm
from store.models import Product


# ✅ الصفحة الرئيسية - عرض المنتجات المتاحة
def home(request):
    products = Product.objects.filter(available=True).order_by('-created_at')
    return render(request, 'home.html', {'products': products})


def header(request):
    return render(request, 'header.html')


def footer(request):
    return render(request, 'footer.html')


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


def logout_view(request):
    logout(request)
    return redirect('home')


def contact(request):
    return render(request, 'core/contact.html')


def privacy_view(request):
    return render(request, 'core/privacy.html')


def terms_view(request):
    return render(request, 'core/terms.html')


def book_lesson(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        grade = request.POST.get("grade")
        subjects = request.POST.getlist("subjects")

        messages.success(request, "✅ تم إرسال طلب الحجز بنجاح! سنتواصل معك قريبًا.")
        return redirect('home')

    return render(request, 'core/booking_form.html')
