from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


# ===============================
# Inline صور المنتج (Cloudinary)
# ===============================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "image", "alt_text", "is_primary", "sort_order")
    readonly_fields = ("preview",)

    def preview(self, obj):
        """
        عرض صورة مصغرة من Cloudinary داخل الـ Admin
        """
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="width:80px;height:auto;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return format_html("<span>{}</span>", "لا توجد صورة")

    preview.short_description = "معاينة"


# ===============================
# Admin المنتج
# ===============================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "is_active",
        "is_featured",
    )
    list_filter = ("is_active", "is_featured", "category")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]


# ===============================
# Admin التصنيفات
# ===============================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


# ===============================
# ✅ Admin متغيرات المنتج (مصَحَّح)
# ===============================
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    تسجيل ProductVariant ضروري لتشغيل autocomplete_fields
    في orders.admin
    """
    list_display = (
        "sku",        # ✔ موجود
        "title",      # ✔ موجود
        "product",
        "price",
        "is_active",
    )
    list_filter = ("is_active", "product")
    search_fields = ("sku", "title", "product__name")
