from __future__ import annotations

from django.db import models
from cloudinary.models import CloudinaryField
from django.urls import reverse


# ✅ التصنيفات للمنتجات
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم التصنيف")

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "تصنيفات"

    def __str__(self) -> str:
        return self.name


# ✅ المنتجات (تابعة للمتجر فقط)
class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم المنتج")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products", verbose_name="التصنيف"
    )
    available = models.BooleanField(default=True, verbose_name="متوفر؟")
    image = CloudinaryField(verbose_name="صورة المنتج", blank=True, null=True)
    description = models.TextField(blank=True, verbose_name="الوصف")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    # ✅ الربط مع دورة لوحة الطالب (Course) — اختياري
    # نستخدم المسار النصي 'students.Course' لتجنب أي دورات استيراد دائرية
    course = models.ForeignKey(
        "students.Course",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
        verbose_name="الدورة المرتبطة (لوحة الطالب)",
        help_text="اختياري: اربط هذا المنتج بدورة ليظهر للطالب تلقائيًا بعد الإتمام."
    )

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "منتجات"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["available"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_available(self) -> bool:
        return self.available

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.pk])
