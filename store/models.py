from django.db import models
from cloudinary.models import CloudinaryField

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "منتجات"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name

    @property
    def is_available(self) -> bool:
        return self.available
