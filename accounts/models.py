from __future__ import annotations

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# ✅ مدقق رقم الجوال / الهاتف
phone_validator = RegexValidator(
    regex=r"^\+?\d{8,15}$",
    message=_("أدخل رقم جوال أو هاتف بصيغة صحيحة (من 8 إلى 15 رقمًا)، ويمكن أن يبدأ بعلامة +.")
)


class CustomerProfile(models.Model):
    """
    ملف تعريف العميل (اختياري)
    لتوسعة بيانات المستخدم بدون التعديل على نموذج المستخدم الافتراضي.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
        verbose_name=_("المستخدم"),
    )

    phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        blank=True,
        verbose_name=_("رقم الجوال"),
    )

    is_marketing_opt_in = models.BooleanField(
        default=False,
        verbose_name=_("موافق على الرسائل التسويقية"),
        help_text=_("هل وافق العميل على استقبال العروض والرسائل التسويقية؟"),
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
        verbose_name = _("ملف عميل")
        verbose_name_plural = _("ملفات العملاء")

    def __str__(self) -> str:
        return f"ملف عميل رقم ({self.user_id})"


class Address(models.Model):
    """
    عناوين الشحن والفواتير الخاصة بالعميل.
    """

    class AddressType(models.TextChoices):
        SHIPPING = "shipping", _("عنوان شحن")
        BILLING = "billing", _("عنوان فواتير")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("المستخدم"),
    )

    type = models.CharField(
        max_length=20,
        choices=AddressType.choices,
        default=AddressType.SHIPPING,
        verbose_name=_("نوع العنوان"),
    )

    full_name = models.CharField(
        max_length=150,
        verbose_name=_("الاسم الكامل"),
    )

    phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        blank=True,
        verbose_name=_("رقم الجوال"),
    )

    country = models.CharField(
        max_length=80,
        default=_("المملكة العربية السعودية"),
        verbose_name=_("الدولة"),
    )

    city = models.CharField(
        max_length=80,
        default=_("الرياض"),
        verbose_name=_("المدينة"),
    )

    district = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_("الحي"),
    )

    street = models.CharField(
        max_length=200,
        verbose_name=_("الشارع"),
    )

    building_no = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_("رقم المبنى"),
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("الرمز البريدي"),
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_("العنوان الافتراضي"),
        help_text=_("تحديد هذا العنوان كعنوان افتراضي"),
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
        verbose_name = _("عنوان")
        verbose_name_plural = _("العناوين")
        indexes = [
            models.Index(fields=["user", "type"]),
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.city} ({self.get_type_display()})"

    def save(self, *args, **kwargs):
        """
        ضمان وجود عنوان افتراضي واحد فقط
        لكل مستخدم ولكل نوع عنوان (شحن / فواتير).
        """
        super().save(*args, **kwargs)

        if self.is_default:
            Address.objects.filter(
                user=self.user,
                type=self.type
            ).exclude(
                pk=self.pk
            ).update(is_default=False)
