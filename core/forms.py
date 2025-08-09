# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from core.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="البريد الإلكتروني",
        widget=forms.EmailInput(attrs={
            "placeholder": "أدخل بريدك الإلكتروني",
            "class": "form-control",
            "autocomplete": "email",
        })
    )

    ROLE_CHOICES = (
        ("student", "طالب"),
        ("teacher", "معلم"),
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        label="نوع الحساب",
    )

    class Meta:
        model = CustomUser
        # وضع الدور قبل كلمات المرور لسهولة الاستخدام
        fields = ["username", "email", "role", "password1", "password2"]
        labels = {
            "username": "اسم المستخدم",
            "password1": "كلمة المرور",
            "password2": "تأكيد كلمة المرور",
        }
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "أدخل اسم المستخدم",
                "class": "form-control",
                "autocomplete": "username",
            }),
            "password1": forms.PasswordInput(attrs={
                "placeholder": "أدخل كلمة المرور",
                "class": "form-control",
                "autocomplete": "new-password",
            }),
            "password2": forms.PasswordInput(attrs={
                "placeholder": "أعد إدخال كلمة المرور",
                "class": "form-control",
                "autocomplete": "new-password",
            }),
        }

    # ✅ تحقق بسيط من عدم تكرار البريد (اختياري لكنه مفيد)
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("هذا البريد مستخدم بالفعل.")
        return email

    # ✅ نحفظ الدور والبريد بشكل صريح
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        user.role = self.cleaned_data.get("role")
        if commit:
            user.save()
        return user
