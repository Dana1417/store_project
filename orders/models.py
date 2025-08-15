# orders/models.py
from __future__ import annotations

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from store.models import Product


class Order(models.Model):
    """
    طلب لمنتج واحد (حسب تصميمك الحالي).
    - نلتقط سعر المنتج وقت إنشاء الطلب في unit_price (مع default=0 لتفادي مشاكل المايجريشن).
    - حالات الطلب لضبط دورة الحياة.
    - طوابع زمنية للإنشاء والتحديث.
    """

    # حالات الطلب
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

    # المستخدم اختياري (طلبات ضيوف)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="single_orders",
        verbose_name="المستخدم",
    )

    # منتج واحد لكل طلب
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # نحمي السجل التاريخي
        related_name="orders",
        verbose_name="المنتج",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="الكمية",
    )

    # لقطة سعر وقت الطلب
    unit_price = models.DecimalField(
        "السعر وقت الطلب",
        max_digits=10,
        decimal_places=2,
        default=0,                        # ✅ يمنع رسالة "Provide a one-off default"
        validators=[MinValueValidator(0)],
        help_text="سعر المنتج وقت إنشاء الطلب (لقطة سعر).",
    )

    status = models.CharField(
        "حالة الطلب",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
    )

    # طوابع زمنية
    created_at = models.DateTimeField("تاريخ الإنشاء", default=timezone.now, db_index=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        user_display = getattr(self.user, "username", "ضيف")
        return f"طلب #{self.id} - {self.product.name} × {self.quantity} بواسطة {user_display}"

    @property
    def total_price(self) -> Decimal:
        return (Decimal(self.unit_price) if self.unit_price is not None else Decimal("0")) * int(self.quantity)

    def set_snapshot_price_if_missing(self) -> None:
        """
        يُستحسن استدعاؤها قبل أول حفظ إذا لم تُمرَّر unit_price من الـ view.
        """
        if self.unit_price in (None, "") or Decimal(self.unit_price) == Decimal("0"):
            # نفترض أن Product.price موجود ومناسب كرقم عشري
            self.unit_price = getattr(self.product, "price", Decimal("0.00"))
