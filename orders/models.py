# orders/models.py
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from store.models import Product


# =========================
#         Order
# =========================
class Order(models.Model):
    """
    طلب رئيسي:
    - يخص مستخدم معيّن.
    - يحتوي على عدة منتجات (عبر OrderItem).
    - يدعم حالات: new / confirmed / paid / canceled.
    """

    STATUS_NEW = "new"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PAID = "paid"
    STATUS_CANCELED = "canceled"

    STATUS_CHOICES = (
        (STATUS_NEW, "جديد"),
        (STATUS_CONFIRMED, "مؤكد"),
        (STATUS_PAID, "مدفوع"),
        (STATUS_CANCELED, "ملغي"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
        verbose_name="المستخدم",
    )

    status = models.CharField(
        "حالة الطلب",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
    )

    created_at = models.DateTimeField("تاريخ الإنشاء", default=timezone.now, db_index=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        user_display = getattr(self.user, "username", "ضيف")
        return f"طلب #{self.pk or '—'} بواسطة {user_display} [{self.get_status_display()}]"

    # ===== خصائص =====
    @property
    def total_price(self) -> Decimal:
        """إجمالي قيمة الطلب"""
        return sum(item.subtotal for item in self.items.all())

    # ===== انتقالات الحالة =====
    @transaction.atomic
    def confirm(self) -> bool:
        if self.status != self.STATUS_NEW:
            return False
        self.status = self.STATUS_CONFIRMED
        self.save(update_fields=["status", "updated_at"])
        return True

    @transaction.atomic
    def pay(self) -> bool:
        if self.status in (self.STATUS_PAID, self.STATUS_CANCELED):
            return False
        self.status = self.STATUS_PAID
        self.save(update_fields=["status", "updated_at"])
        return True

    @transaction.atomic
    def cancel(self) -> bool:
        if self.status in (self.STATUS_PAID, self.STATUS_CANCELED):
            return False
        self.status = self.STATUS_CANCELED
        self.save(update_fields=["status", "updated_at"])
        return True

    # ===== فلاتر سريعة =====
    def is_paid(self) -> bool:
        return self.status == self.STATUS_PAID

    def is_confirmed(self) -> bool:
        return self.status == self.STATUS_CONFIRMED

    def is_canceled(self) -> bool:
        return self.status == self.STATUS_CANCELED

    def can_pay(self) -> bool:
        return self.status in (self.STATUS_NEW, self.STATUS_CONFIRMED)


# =========================
#       OrderItem
# =========================
class OrderItem(models.Model):
    """
    عنصر داخل الطلب:
    - يربط المنتج بالطلب.
    - يلتقط السعر وقت الحجز.
    """

    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="الطلب",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="المنتج",
    )
    quantity = models.PositiveIntegerField(
        "الكمية",
        default=1,
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        "سعر الوحدة وقت الطلب",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=Decimal("0.00"),
    )

    class Meta:
        verbose_name = "عنصر طلب"
        verbose_name_plural = "عناصر الطلب"
        unique_together = ("order", "product")

    def __str__(self):
        return f"{self.product} × {self.quantity} (طلب #{self.order_id})"

    @property
    def subtotal(self) -> Decimal:
        """الإجمالي لهذا العنصر"""
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        """تثبيت سعر المنتج عند أول إضافة للطلب"""
        if not self.pk and (not self.unit_price or self.unit_price == 0):
            self.unit_price = getattr(self.product, "price", Decimal("0.00")) or Decimal("0.00")
        super().save(*args, **kwargs)
