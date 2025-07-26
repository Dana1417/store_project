from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'ordered_at')
    list_filter = ('ordered_at',)
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('ordered_at',)
