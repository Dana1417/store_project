from django.db import models
from django.conf import settings  # ✅ نستخدم settings.AUTH_USER_MODEL بدلًا من User مباشرة
from store.models import Product

class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="المستخدم"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="المنتج"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="الكمية"
    )
    ordered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الطلب"
    )

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"

    def __str__(self):
        return f"طلب {self.product.name} بواسطة {self.user.username}"
