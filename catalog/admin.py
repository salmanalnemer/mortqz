from __future__ import annotations

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Category, Product, ProductVariant, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "sort_order", "slug", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("preview", "image", "alt_text", "is_primary", "sort_order")
    readonly_fields = ("preview",)
    ordering = ("sort_order",)

    def preview(self, obj: ProductImage):
        if obj and getattr(obj, "image", None):
            try:
                return format_html('<img src="{}" style="height:60px;border-radius:8px;" />', obj.image.url)
            except Exception:
                return "—"
        return "—"

    preview.short_description = "معاينة"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = (
        "sku",
        "title",
        "is_active",
        "price",
        "compare_at_price",
        "track_inventory",
        "stock_quantity",
        "color",
        "size",
    )
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "is_active",
        "is_featured",
        "price",
        "currency",
        "stock_quantity",
        "variants_count",
        "updated_at",
    )
    list_filter = ("is_active", "is_featured", "category")
    search_fields = ("name", "slug", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVariantInline]
    ordering = ("-updated_at",)
    list_select_related = ("category",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_variants_count=Count("variants"))

    def variants_count(self, obj: Product):
        return getattr(obj, "_variants_count", 0)

    variants_count.short_description = "عدد المتغيرات"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "title", "is_active", "price", "currency", "stock_quantity", "updated_at")
    list_filter = ("is_active", "currency")
    search_fields = ("sku", "product__name", "title")
    autocomplete_fields = ("product",)
    ordering = ("-updated_at",)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "is_primary", "sort_order", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("product__name", "alt_text")
    autocomplete_fields = ("product",)
    ordering = ("product", "sort_order")
