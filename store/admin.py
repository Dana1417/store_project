from django.contrib import admin
from .models import Category, Product, Booking


# =========================
#   إدارة التصنيفات
# =========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 25


# =========================
#   إدارة المنتجات
# =========================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # الأعمدة في قائمة المنتجات
    list_display = ("id", "name", "price", "category", "available", "created_at")
    list_filter = ("available", "category", "created_at")
    search_fields = ("name", "description")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 25

    # تنظيم الحقول في صفحة الإضافة/التعديل
    fieldsets = (
        ("البيانات الأساسية", {
            "fields": ("name", "price", "category", "available")
        }),
        ("الوسائط", {
            "fields": ("image",),
            "description": "ارفع صورة المنتج (يُفضل أبعاد 4:3 أو 16:9)."
        }),
        ("الوصف", {
            "fields": ("description",),
        }),
        ("أخرى", {
            "fields": ("created_at",),
        }),
    )
    readonly_fields = ("created_at",)


# =========================
#   إدارة الحجوزات
# =========================
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone", "stage", "course", "created_at")
    list_filter = ("course", "created_at")
    search_fields = ("full_name", "phone", "stage", "subjects")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 25
