from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


class Cart(models.Model):
    """
    سلة: إما لمستخدم مسجل أو لزائر عبر session_key.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carts",
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سلة"
        verbose_name_plural = "السلات"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["session_key"]),
        ]

    def __str__(self) -> str:
        return f"Cart(user={self.user_id}, session={self.session_key})"

    def clean(self):
        # قاعدة منطقية: لازم user أو session_key يكون موجود
        if not self.user_id and not self.session_key:
            raise ValueError("Cart must have either a user or a session_key.")


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")

    # المنتج أو المتغير (Variant)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True,
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True,
    )

    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "عنصر سلة"
        verbose_name_plural = "عناصر السلة"
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(product__isnull=False) & models.Q(variant__isnull=True)) |
                        (models.Q(product__isnull=True) & models.Q(variant__isnull=False)),
                name="orders_cartitem_requires_product_or_variant",
            ),

            models.UniqueConstraint(
                fields=["cart", "product", "variant"],
                name="orders_unique_cartitem_per_cart_product_variant",
            ),
        ]

    def __str__(self) -> str:
        ref = self.variant.sku if self.variant_id else f"product:{self.product_id}"
        return f"CartItem({ref}) x{self.quantity}"


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "مسودة"
        PENDING_PAYMENT = "pending_payment", "بانتظار الدفع"
        PAID = "paid", "مدفوع"
        PROCESSING = "processing", "قيد التجهيز"
        SHIPPED = "shipped", "تم الشحن"
        DELIVERED = "delivered", "تم التسليم"
        CANCELLED = "cancelled", "ملغي"
        REFUNDED = "refunded", "مسترجع"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)

    currency = models.CharField(max_length=10, default="SAR")

    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )
    shipping_fee = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )
    discount_total = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )

    # عنوان الشحن (من accounts)
    shipping_address = models.ForeignKey(
        "accounts.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_as_shipping",
    )

    notes = models.CharField(max_length=400, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Order({self.order_number})"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # رقم طلب بسيط: YYYY + 8 أحرف/أرقام
            year = timezone.now().strftime("%Y")
            rnd = get_random_string(8, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
            self.order_number = f"{year}{rnd}"
        super().save(*args, **kwargs)

    def recalc_totals(self):
        """
        إعادة احتساب الإجماليات من عناصر الطلب.
        """
        items = self.items.all()
        subtotal = Decimal("0.00")
        for it in items:
            subtotal += (it.unit_price * it.quantity)

        self.subtotal = subtotal
        computed_total = subtotal + self.shipping_fee - self.discount_total
        if computed_total < 0:
            computed_total = Decimal("0.00")
        self.total = computed_total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    # ربط اختياري بالمنتج/المتغير للاحتفاظ بالمرجع
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    # Snapshot وقت الشراء (مهم حتى لو تغير السعر لاحقًا)
    product_name = models.CharField(max_length=220)
    sku = models.CharField(max_length=64, blank=True)

    currency = models.CharField(max_length=10, default="SAR")
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )
    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name = "عنصر طلب"
        verbose_name_plural = "عناصر الطلب"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["sku"]),
        ]
        constraints = [
            models.CheckConstraint(
            condition=models.Q(quantity__gte=1),
            name="orders_orderitem_quantity_gte_1",
        )

        ]

    def __str__(self) -> str:
        return f"{self.product_name} x{self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


class Payment(models.Model):
    class Status(models.TextChoices):
        INITIATED = "initiated", "مبدئي"
        PENDING = "pending", "معلق"
        SUCCEEDED = "succeeded", "ناجح"
        FAILED = "failed", "فشل"
        REFUNDED = "refunded", "مسترجع"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")

    provider = models.CharField(max_length=50, default="manual")  # لاحقًا: tap/stripe/paypal...
    transaction_id = models.CharField(max_length=120, blank=True, db_index=True)

    currency = models.CharField(max_length=10, default="SAR")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)

    raw_response = models.JSONField(null=True, blank=True)  # تخزين رد بوابة الدفع (اختياري)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "عملية دفع"
        verbose_name_plural = "المدفوعات"
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["transaction_id"]),
        ]

    def __str__(self) -> str:
        return f"Payment({self.order_id}, {self.status})"


class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "بانتظار الشحن"
        SHIPPED = "shipped", "تم الشحن"
        DELIVERED = "delivered", "تم التسليم"
        RETURNED = "returned", "مرتجع"
        CANCELLED = "cancelled", "ملغي"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="shipment")

    carrier = models.CharField(max_length=80, blank=True)  # شركة الشحن
    tracking_number = models.CharField(max_length=120, blank=True, db_index=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "شحنة"
        verbose_name_plural = "الشحنات"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["tracking_number"]),
        ]

    def __str__(self) -> str:
        return f"Shipment({self.order_id}, {self.status})"
