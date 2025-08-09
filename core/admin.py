from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ContactMessage

# ✅ تسجيل نموذج المستخدم المخصص
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية', {'fields': ('role',)}),
    )

# ✅ تسجيل نموذج رسائل التواصل
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email')
    readonly_fields = ('created_at',)
