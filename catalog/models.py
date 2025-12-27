from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    """
    تصنيفات المنتجات (تدعم شجرة: تصنيف رئيسي/فرعي).
    """
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "التصنيفات"
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
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # السعر الأساسي (لمنتج بدون variants)
    currency = models.CharField(max_length=10, default="SAR")
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        null=True,
        blank=True,
    )

    # المخزون الأساسي (لمنتج بدون variants)
    track_inventory = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
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
    Variant (SKU) مثل: لون/مقاس.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    sku = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=120, blank=True)  # مثال: "Black / XL"
    is_active = models.BooleanField(default=True)

    currency = models.CharField(max_length=10, default="SAR")
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        null=True,
        blank=True,
    )

    track_inventory = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    # خصائص بسيطة بدون تعقيد (تقدر تطورها لاحقًا)
    color = models.CharField(max_length=60, blank=True)
    size = models.CharField(max_length=60, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "متغير منتج"
        verbose_name_plural = "متغيرات المنتجات"
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["product", "is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["product", "title"], name="catalog_unique_variant_title_per_product"),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.sku}"


class ProductImage(models.Model):
    """
    صور المنتج (تحتاج Pillow لاستخدام ImageField).
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")

    image = models.ImageField(upload_to="products/%Y/%m/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name = "صورة منتج"
        verbose_name_plural = "صور المنتجات"
        indexes = [
            models.Index(fields=["product", "is_primary"]),
            models.Index(fields=["product", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"Image({self.product_id})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_primary=False)
