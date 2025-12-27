from __future__ import annotations

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomerProfile, Address


User = get_user_model()


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    extra = 0
    verbose_name_plural = "ملف العميل"


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = (
        "type",
        "full_name",
        "phone",
        "country",
        "city",
        "district",
        "street",
        "building_no",
        "postal_code",
        "is_default",
    )
    readonly_fields = ()
    show_change_link = True


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "full_name", "phone", "city", "is_default", "updated_at")
    list_filter = ("type", "city", "is_default", "country")
    search_fields = ("full_name", "phone", "city", "district", "street", "user__username", "user__email")
    autocomplete_fields = ("user",)
    ordering = ("-updated_at",)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone", "is_marketing_opt_in", "created_at", "updated_at")
    list_filter = ("is_marketing_opt_in",)
    search_fields = ("user__username", "user__email", "phone")
    autocomplete_fields = ("user",)
    ordering = ("-updated_at",)


# تحسين إدارة المستخدم الافتراضي + إضافة Inlines (ملف العميل + العناوين)
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [CustomerProfileInline, AddressInline]

    # إضافات للبحث/العرض
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    # لتجنب مشاكل لو كانت حقول البريد غير مطلوبة
    fieldsets = DjangoUserAdmin.fieldsets
    add_fieldsets = DjangoUserAdmin.add_fieldsets
