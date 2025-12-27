from __future__ import annotations

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


phone_validator = RegexValidator(
    regex=r"^\+?\d{8,15}$",
    message="أدخل رقم جوال/هاتف بصيغة صحيحة (8 إلى 15 رقمًا) ويمكن أن يبدأ بـ +."
)


class CustomerProfile(models.Model):
    """
    ملف تعريف العميل (اختياري) لتوسعة بيانات المستخدم بدون تعديل User الافتراضي.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    phone = models.CharField(max_length=20, validators=[phone_validator], blank=True)
    is_marketing_opt_in = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ملف عميل"
        verbose_name_plural = "ملفات العملاء"

    def __str__(self) -> str:
        return f"CustomerProfile({self.user_id})"


class Address(models.Model):
    """
    عناوين الشحن/الفواتير للعميل.
    """
    class AddressType(models.TextChoices):
        SHIPPING = "shipping", "شحن"
        BILLING = "billing", "فواتير"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    type = models.CharField(max_length=20, choices=AddressType.choices, default=AddressType.SHIPPING)

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, validators=[phone_validator], blank=True)

    country = models.CharField(max_length=80, default="Saudi Arabia")
    city = models.CharField(max_length=80, default="Riyadh")
    district = models.CharField(max_length=120, blank=True)
    street = models.CharField(max_length=200)
    building_no = models.CharField(max_length=30, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "عنوان"
        verbose_name_plural = "العناوين"
        indexes = [
            models.Index(fields=["user", "type"]),
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.city} ({self.type})"

    def save(self, *args, **kwargs):
        """
        ضمان عنوان افتراضي واحد لكل (user, type).
        """
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(user=self.user, type=self.type).exclude(pk=self.pk).update(is_default=False)
