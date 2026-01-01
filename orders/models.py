from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

#   نماذج الطلبات: سلة، طلب، عناصر الطلب، دفع، شحنة
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
        verbose_name=_("المستخدم"),
    )
    session_key = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        verbose_name=_("مفتاح الجلسة"),
        help_text=_("يُستخدم لربط السلة بالزائر غير المسجل عبر Session."),
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
        verbose_name = _("سلة")
        verbose_name_plural = _("السلات")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["session_key"]),
        ]

    def __str__(self) -> str:
        return f"سلة (مستخدم={self.user_id}, جلسة={self.session_key or '-'})"

    def clean(self):
        # قاعدة منطقية: لازم user أو session_key يكون موجود
        if not self.user_id and not self.session_key:
            raise ValidationError(_("يجب أن تحتوي السلة على مستخدم أو مفتاح جلسة (session_key)."))

# نموذج عنصر السلة
class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("السلة"),
    )

    # المنتج أو المتغير (Variant)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True,
        verbose_name=_("المنتج"),
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True,
        verbose_name=_("متغير المنتج"),
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("الكمية"),
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
        verbose_name = _("عنصر سلة")
        verbose_name_plural = _("عناصر السلة")
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(product__isnull=False) & models.Q(variant__isnull=True))
                    | (models.Q(product__isnull=True) & models.Q(variant__isnull=False))
                ),
                name="orders_cartitem_requires_product_or_variant",
            ),
            models.UniqueConstraint(
                fields=["cart", "product", "variant"],
                name="orders_unique_cartitem_per_cart_product_variant",
            ),
        ]

    def __str__(self) -> str:
        ref = self.variant.sku if self.variant_id else f"product:{self.product_id}"
        return f"عنصر سلة ({ref}) × {self.quantity}"

# نموذج الطلب
class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("مسودة")
        PENDING_PAYMENT = "pending_payment", _("بانتظار الدفع")
        PAID = "paid", _("مدفوع")
        PROCESSING = "processing", _("قيد التجهيز")
        SHIPPED = "shipped", _("تم الشحن")
        DELIVERED = "delivered", _("تم التسليم")
        CANCELLED = "cancelled", _("ملغي")
        REFUNDED = "refunded", _("مسترجع")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("المستخدم"),
    )

    order_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name=_("رقم الطلب"),
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("حالة الطلب"),
    )

    currency = models.CharField(
        max_length=10,
        default="SAR",
        verbose_name=_("العملة"),
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
        verbose_name=_("المجموع الفرعي"),
    )
    shipping_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
        verbose_name=_("رسوم الشحن"),
    )
    discount_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
        verbose_name=_("إجمالي الخصم"),
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
        verbose_name=_("الإجمالي"),
    )

    # عنوان الشحن (من accounts)
    shipping_address = models.ForeignKey(
        "accounts.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_as_shipping",
        verbose_name=_("عنوان الشحن"),
    )

    notes = models.CharField(
        max_length=400,
        blank=True,
        verbose_name=_("ملاحظات"),
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
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاريخ الدفع"),
    )

    class Meta:
        verbose_name = _("طلب")
        verbose_name_plural = _("الطلبات")
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"طلب رقم ({self.order_number})"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # رقم طلب بسيط: YYYY + 8 أحرف/أرقام بدون رموز ملتبسة
            year = timezone.now().strftime("%Y")
            rnd = get_random_string(8, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
            self.order_number = f"{year}{rnd}"
        super().save(*args, **kwargs)

    def recalc_totals(self):
        """
        إعادة احتساب الإجماليات من عناصر الطلب.
        (لا يقوم بالحفظ تلقائيًا)
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

# نموذج عنصر الطلب
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("الطلب"),
    )

    # ربط اختياري بالمنتج/المتغير للاحتفاظ بالمرجع
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name=_("المنتج"),
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name=_("متغير المنتج"),
    )

    # Snapshot وقت الشراء (مهم حتى لو تغير السعر لاحقًا)
    product_name = models.CharField(
        max_length=220,
        verbose_name=_("اسم المنتج وقت الشراء"),
    )
    sku = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("رمز SKU"),
    )

    currency = models.CharField(
        max_length=10,
        default="SAR",
        verbose_name=_("العملة"),
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
        verbose_name=_("سعر الوحدة"),
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("الكمية"),
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name=_("تاريخ الإضافة"),
    )

    class Meta:
        verbose_name = _("عنصر طلب")
        verbose_name_plural = _("عناصر الطلب")
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["sku"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="orders_orderitem_quantity_gte_1",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product_name} × {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

# نموذج الدفع
class Payment(models.Model):
    class Status(models.TextChoices):
        INITIATED = "initiated", _("مبدئي")
        PENDING = "pending", _("معلق")
        SUCCEEDED = "succeeded", _("ناجح")
        FAILED = "failed", _("فشل")
        REFUNDED = "refunded", _("مسترجع")

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("الطلب"),
    )

    provider = models.CharField(
        max_length=50,
        default="manual",
        verbose_name=_("مزود الدفع"),
        help_text=_("مثال لاحقًا: tap / stripe / paypal ..."),
    )
    transaction_id = models.CharField(
        max_length=120,
        blank=True,
        db_index=True,
        verbose_name=_("معرّف العملية"),
    )

    currency = models.CharField(
        max_length=10,
        default="SAR",
        verbose_name=_("العملة"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
        verbose_name=_("المبلغ"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INITIATED,
        verbose_name=_("حالة الدفع"),
    )

    raw_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("الاستجابة الخام"),
        help_text=_("تخزين رد بوابة الدفع (اختياري)."),
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
        verbose_name = _("عملية دفع")
        verbose_name_plural = _("المدفوعات")
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["transaction_id"]),
        ]

    def __str__(self) -> str:
        return f"دفع (طلب={self.order_id}, حالة={self.get_status_display()})"

# نموذج الشحنة
class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("بانتظار الشحن")
        SHIPPED = "shipped", _("تم الشحن")
        DELIVERED = "delivered", _("تم التسليم")
        RETURNED = "returned", _("مرتجع")
        CANCELLED = "cancelled", _("ملغي")

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="shipment",
        verbose_name=_("الطلب"),
    )

    carrier = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_("شركة الشحن"),
    )
    tracking_number = models.CharField(
        max_length=120,
        blank=True,
        db_index=True,
        verbose_name=_("رقم التتبع"),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("حالة الشحنة"),
    )

    shipped_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاريخ الشحن"),
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاريخ التسليم"),
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
        verbose_name = _("شحنة")
        verbose_name_plural = _("الشحنات")
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["tracking_number"]),
        ]

    def __str__(self) -> str:
        return f"شحنة (طلب={self.order_id}, حالة={self.get_status_display()})"
