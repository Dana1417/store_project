from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse

from .forms import CustomUserCreationForm
from store.models import Product
from students.models import Student  # ✅ التصحيح هنا

# ✅ الصفحة الرئيسية - عرض المنتجات المتاحة
def home(request):
    products = Product.objects.filter(available=True).order_by('-created_at')
    return render(request, 'home.html', {'products': products})

# ✅ تضمين الهيدر والفوتر
def header(request):
    return render(request, 'header.html')

def footer(request):
    return render(request, 'footer.html')

# ✅ إنشاء حساب جديد + توجيه حسب الدور
def register_view(request):
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "🎉 تم إنشاء الحساب بنجاح، مرحبًا بك!")

            # ⤴️ احترام next إن وُجد
            if next_url:
                return redirect(next_url)

            # 👇 التأكد من إنشاء سجل الطالب فقط (بدون stage لأنه غير موجود في الموديل)
            if user.role == 'student':
                Student.objects.get_or_create(user=user)
                return redirect('students:dashboard')        # ✅ التصحيح
            elif user.role == 'teacher':
                return redirect('store:teacher_dashboard')    # ✅ التصحيح
            else:
                return redirect('home')
        else:
            messages.error(request, "تحقق من الحقول المدخلة.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'core/register.html', {'form': form})

# ✅ تسجيل الدخول + توجيه حسب الدور
def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next')

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
                messages.success(request, "✅ تم تسجيل الدخول بنجاح!")

                # ⤴️ احترام next إن وُجد
                if next_url:
                    return redirect(next_url)

                if user.role == 'student':
                    Student.objects.get_or_create(user=user)  # ✅ بدون stage
                    return redirect('students:dashboard')      # ✅ التصحيح
                elif user.role == 'teacher':
                    return redirect('store:teacher_dashboard')  # ✅ التصحيح
                else:
                    return redirect('home')
        messages.error(request, "اسم المستخدم أو كلمة المرور غير صحيحة.")
    else:
        form = AuthenticationForm()

    return render(request, 'core/login.html', {'form': form})

# ✅ تسجيل الخروج
def logout_view(request):
    logout(request)
    messages.info(request, "👋 تم تسجيل الخروج.")
    return redirect('home')

# ✅ صفحات عامة
def contact(request):
    return render(request, 'core/contact.html')

def privacy_view(request):
    return render(request, 'core/privacy.html')

def terms_view(request):
    return render(request, 'core/terms.html')

# ✅ نموذج حجز درس (بسيط)
def book_lesson(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        grade = request.POST.get("grade")
        subjects = request.POST.getlist("subjects")
        # TODO: احفظ الطلب في قاعدة البيانات إن رغبت
        messages.success(request, "✅ تم إرسال طلب الحجز بنجاح! سنتواصل معك قريبًا.")
        return redirect('home')

    return render(request, 'core/booking_form.html')
