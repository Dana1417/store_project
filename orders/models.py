# orders/models.py
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from store.models import Product


class Order(models.Model):
    """
    نموذج طلب لمنتج واحد:
    - يلتقط سعر المنتج وقت إنشاء الطلب في unit_price (لقطة سعر).
    - يدعم حالات دورة حياة الطلب: new/confirmed/paid/canceled.
    - يحتوي دوال انتقال حالة آمنة (idempotent) مع حفظ ذرّي.
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

    # المستخدم (قد يكون None لطلبات الضيوف)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="single_orders",
        verbose_name="المستخدم",
    )

    # منتج واحد لكل طلب
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # نحافظ على تاريخ الطلب حتى لو تعطل المنتج لاحقًا
        related_name="orders",
        verbose_name="المنتج",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="الكمية",
    )

    # لقطة سعر وقت إنشاء الطلب (لمنع تغيّر السعر لاحقًا من التأثير)
    unit_price = models.DecimalField(
        "السعر وقت الطلب",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
        help_text="سعر المنتج لحظة إنشاء الطلب (لقطة سعر).",
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
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["product"]),
        ]

    # ========= واجهة نصيّة =========
    def __str__(self) -> str:
        user_display = getattr(self.user, "username", "ضيف")
        return f"طلب #{self.pk or '—'} - {self.product} × {self.quantity} بواسطة {user_display} [{self.status}]"

    # ========= خصائص مساعدة =========
    @property
    def total_price(self) -> Decimal:
        """
        مجموع الطلب (الكمية × لقطة السعر).
        """
        q = int(self.quantity or 0)
        p = Decimal(self.unit_price or 0)
        return p * q

    def snapshot_price(self) -> Decimal:
        """
        إرجاع لقطة السعر المقترحة من المنتج (بدون حفظ).
        """
        return Decimal(getattr(self.product, "price", Decimal("0.00")) or Decimal("0.00"))

    def set_snapshot_price_if_missing(self) -> None:
        """
        يضبط unit_price من سعر المنتج إذا كان صفرًا/فارغًا.
        """
        try:
            price = Decimal(self.unit_price or 0)
        except Exception:
            price = Decimal("0.00")

        if price == Decimal("0.00"):
            self.unit_price = self.snapshot_price()

    # ========= قيود وتنظيف =========
    def clean(self):
        super().clean()
        if self.quantity < 1:
            raise ValueError("الكمية يجب أن تكون 1 على الأقل.")

    # ========= حفظ مخصّص =========
    def save(self, *args, **kwargs):
        # قبل الحفظ الأول نلتقط السعر لو كان صفر
        if not self.pk:
            self.set_snapshot_price_if_missing()
        super().save(*args, **kwargs)

    # ========= انتقالات الحالة (آمنة و idempotent) =========
    @transaction.atomic
    def confirm(self) -> bool:
        """
        ينقل الطلب إلى confirmed إن كان في new.
        يعيد True لو حدث تغيير فعلي.
        """
        if self.status != self.STATUS_NEW:
            return False
        self.status = self.STATUS_CONFIRMED
        self.save(update_fields=["status", "updated_at"])
        return True

    @transaction.atomic
    def pay(self) -> bool:
        """
        ينقل الطلب إلى paid إن لم يكن ملغيًا.
        مفيد عند محاكاة الدفع أو عند استقبال Webhook.
        """
        if self.status == self.STATUS_CANCELED:
            return False
        if self.status == self.STATUS_PAID:
            return False
        self.set_snapshot_price_if_missing()  # تأكيد وجود لقطة سعر
        self.status = self.STATUS_PAID
        self.save(update_fields=["status", "unit_price", "updated_at"])
        return True

    @transaction.atomic
    def cancel(self) -> bool:
        """
        يلغي الطلب إن لم يكن مدفوعًا مسبقًا.
        """
        if self.status in (self.STATUS_PAID, self.STATUS_CANCELED):
            return False
        self.status = self.STATUS_CANCELED
        self.save(update_fields=["status", "updated_at"])
        return True

    # ========= واجهة مناسبة للـ admin/العروض =========
    def display_user(self) -> str:
        return getattr(self.user, "get_full_name", lambda: "")() or getattr(self.user, "username", "ضيف")

    def display_product(self) -> str:
        return str(self.product)

    def display_status(self) -> str:
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    # ========= سناد محتمل للـ signals =========
    def is_paid(self) -> bool:
        return self.status == self.STATUS_PAID

    def is_confirmed(self) -> bool:
        return self.status == self.STATUS_CONFIRMED

    def is_canceled(self) -> bool:
        return self.status == self.STATUS_CANCELED

    def can_pay(self) -> bool:
        return self.status in (self.STATUS_NEW, self.STATUS_CONFIRMED)
