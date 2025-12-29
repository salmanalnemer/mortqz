from __future__ import annotations

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .admin_widgets import CloudinaryPublicIdWidget
from .models import Category, Product, ProductImage, ProductVariant


# --------- Forms ---------
class ProductImageAdminForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = "__all__"
        widgets = {
            "image_public_id": CloudinaryPublicIdWidget(
                attrs={"style": "width:100%;max-width:520px"}
            ),
        }


# --------- Inlines ---------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageAdminForm
    extra = 1
    fields = ("preview", "image_public_id", "alt_text", "is_primary", "sort_order")
    readonly_fields = ("preview",)

    def preview(self, obj):
        """
        معاينة صورة Cloudinary من public_id
        """
        if obj and getattr(obj, "image_public_id", None):
            cloud_name = "duv2jsooa"  # نفس CLOUDINARY_CLOUD_NAME عندك
            url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{obj.image_public_id}"
            return format_html(
                '<img src="{}" style="width:80px;height:auto;border-radius:8px;border:1px solid #eee" />',
                url,
            )

        # ✅ لا تستخدم format_html بدون args/kwargs في Django 6.0
        return mark_safe('<span style="color:#999;">لا توجد صورة</span>')

    preview.short_description = "معاينة"


# --------- Admin: Product ---------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_active", "is_featured")
    list_filter = ("is_active", "is_featured", "category")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]


# --------- Admin: Category ---------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


# --------- Admin: ProductVariant ---------
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "title", "price", "is_active")
    list_filter = ("is_active", "product")
    search_fields = ("sku", "title", "product__name")
