from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    تصنيفات المنتجات (تدعم شجرة: تصنيف رئيسي/فرعي).
    """

    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name=_("اسم التصنيف"),
    )
    slug = models.SlugField(
        max_length=140,
        unique=True,
        blank=True,
        verbose_name=_("المعرّف (Slug)"),
        help_text=_("يُستخدم في الرابط، ويُنشأ تلقائيًا إذا تُرك فارغًا."),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("التصنيف الأب"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("نشط"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("ترتيب العرض"),
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name=_("تاريخ الإنشاء"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("آخر تحديث"),
    )

    class Meta:
        verbose_name = _("تصنيف")
        verbose_name_plural = _("التصنيفات")
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=True)
            self.slug = base or f"category-{int(timezone.now().timestamp())}"
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    المنتج الأساسي.
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_("اسم المنتج"),
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        verbose_name=_("المعرّف (Slug)"),
        help_text=_("يُستخدم في الرابط، ويُنشأ تلقائيًا إذا تُرك فارغًا."),
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name=_("التصنيف"),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("الوصف"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("نشط"),
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("مميز"),
        help_text=_("إظهار المنتج في الواجهة كمنتج مميز."),
    )

    # السعر الأساسي (لمنتج بدون variants)
    currency = models.CharField(
        max_length=10,
        default="SAR",
        verbose_name=_("العملة"),
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
        verbose_name=_("السعر"),
    )
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        null=True,
        blank=True,
        verbose_name=_("سعر قبل الخصم"),
        help_text=_("اختياري: إذا وضعته يظهر كسعر قديم للمقارنة."),
    )

    # المخزون الأساسي (لمنتج بدون variants)
    track_inventory = models.BooleanField(
        default=True,
        verbose_name=_("تتبع المخزون"),
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_("كمية المخزون"),
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name=_("تاريخ الإضافة"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("آخر تحديث"),
    )

    class Meta:
        verbose_name = _("منتج")
        verbose_name_plural = _("المنتجات")
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["category", "is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(compare_at_price__isnull=True) | models.Q(compare_at_price__gte=0),
                name="catalog_product_compare_at_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def has_variants(self) -> bool:
        return self.variants.filter(is_active=True).exists()

    def get_current_price(self) -> Decimal:
        """
        إذا عندك Variants لاحقًا تقدر تعتمد سعر أول Variant نشط،
        لكن هنا نرجع سعر المنتج الأساسي.
        """
        return self.price

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=True)
            self.slug = base or f"product-{int(timezone.now().timestamp())}"
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    """
    متغير منتج (SKU) مثل: لون/مقاس.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name=_("المنتج"),
    )

    sku = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=_("رمز SKU"),
    )
    title = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_("عنوان المتغير"),
        help_text=_('مثال: "أسود / XL"'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("نشط"),
    )

    currency = models.CharField(
        max_length=10,
        default="SAR",
        verbose_name=_("العملة"),
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
        verbose_name=_("السعر"),
    )
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        null=True,
        blank=True,
        verbose_name=_("سعر قبل الخصم"),
    )

    track_inventory = models.BooleanField(
        default=True,
        verbose_name=_("تتبع المخزون"),
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_("كمية المخزون"),
    )

    # خصائص بسيطة بدون تعقيد (تقدر تطورها لاحقًا)
    color = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_("اللون"),
    )
    size = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_("المقاس"),
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name=_("تاريخ الإضافة"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("آخر تحديث"),
    )

    class Meta:
        verbose_name = _("متغير منتج")
        verbose_name_plural = _("متغيرات المنتجات")
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["product", "is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "title"],
                name="catalog_unique_variant_title_per_product",
            ),
        ]

    def __str__(self) -> str:
        # عرض أنظف في لوحة التحكم
        label = self.title or self.sku
        return f"{self.product.name} - {label}"


class ProductImage(models.Model):
    """
    صور المنتج (تحتاج Pillow لاستخدام ImageField).
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("المنتج"),
    )

    image = models.ImageField(
        upload_to="products/%Y/%m/",
        verbose_name=_("الصورة"),
    )
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("النص البديل"),
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("صورة رئيسية"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("ترتيب العرض"),
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name=_("تاريخ الإضافة"),
    )

    class Meta:
        verbose_name = _("صورة منتج")
        verbose_name_plural = _("صور المنتجات")
        indexes = [
            models.Index(fields=["product", "is_primary"]),
            models.Index(fields=["product", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"صورة المنتج ({self.product_id})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_primary=False)
