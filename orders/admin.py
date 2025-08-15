# orders/admin.py
from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # اعرض أهم الحقول الموجودة فعليًا في الموديل
    list_display = (
        "id",
        "user_display",
        "product",
        "quantity",
        "unit_price",
        "total_price_display",
        "status",
        "created_at",
    )
    list_select_related = ("user", "product")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email", "product__name")
    ordering = ("-created_at",)

    # حقول للقراءة فقط (موجودة فعلًا)
    readonly_fields = ("created_at", "updated_at", "total_price_display")

    fieldsets = (
        ("الأساسية", {
            "fields": ("user", "product", "quantity", "unit_price", "status")
        }),
        ("قراءة فقط", {
            "fields": ("total_price_display", "created_at", "updated_at")
        }),
        ("ملاحظات", {
            "fields": (),  # لو عندك حقول إضافية لاحقًا
        }),
    )

    def user_display(self, obj):
        return getattr(obj.user, "username", "ضيف")
    user_display.short_description = "المستخدم"

    def total_price_display(self, obj):
        return obj.total_price
    total_price_display.short_description = "الإجمالي"
