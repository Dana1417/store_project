from django.db import models
from cloudinary.models import CloudinaryField
from django.conf import settings  # استخدام المستخدم المخصص بدلاً من User


# ✅ التصنيفات للمنتجات
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم التصنيف")

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "تصنيفات"

    def __str__(self):
        return self.name


# ✅ المنتجات
class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم المنتج")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="التصنيف")
    available = models.BooleanField(default=True, verbose_name="متوفر؟")
    image = CloudinaryField(verbose_name="صورة المنتج", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "منتجات"

    def __str__(self):
        return self.name

    @property
    def is_available(self):
        return self.available


# ✅ الدورات
class Course(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم الدورة")
    teams_link = models.URLField(verbose_name="رابط Microsoft Teams")

    class Meta:
        verbose_name = "دورة"
        verbose_name_plural = "دورات"

    def __str__(self):
        return self.name


# ✅ الطالب
class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="المستخدم"
    )
    stage = models.CharField(
        max_length=100,
        verbose_name="المرحلة الدراسية"
    )
    courses = models.ManyToManyField(
        Course,
        verbose_name="الدورات المسجلة",
        blank=True
    )

    class Meta:
        verbose_name = "طالب"
        verbose_name_plural = "طلاب"

    def __str__(self):
        return self.user.get_full_name() or self.user.username
