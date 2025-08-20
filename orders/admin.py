# orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """لعرض عناصر الطلب داخل صفحة الطلب"""
    model = OrderItem
    extra = 0
    readonly_fields = ("subtotal",)
    fields = ("product", "quantity", "unit_price", "subtotal")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """إدارة الطلبات"""
    list_display = (
        "id",
        "user_display",
        "status",
        "total_price_display",
        "created_at",
    )
    list_select_related = ("user",)
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email")
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at", "total_price_display")

    fieldsets = (
        ("الأساسية", {
            "fields": ("user", "status")
        }),
        ("معلومات إضافية", {
            "fields": ("total_price_display", "created_at", "updated_at"),
        }),
    )

    inlines = [OrderItemInline]

    # عرض المستخدم
    def user_display(self, obj):
        return getattr(obj.user, "username", "ضيف")
    user_display.short_description = "المستخدم"

    # عرض الإجمالي
    def total_price_display(self, obj):
        return obj.total_price
    total_price_display.short_description = "الإجمالي"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """إدارة عناصر الطلب"""
    list_display = ("id", "order", "product", "quantity", "unit_price", "subtotal")
    list_select_related = ("order", "product")
    search_fields = ("order__id", "product__name")
    ordering = ("-id",)

    readonly_fields = ("subtotal",)
