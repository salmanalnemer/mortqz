from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Cart, CartItem, Order, OrderItem, Payment, Shipment


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("product", "variant", "quantity", "updated_at")
    autocomplete_fields = ("product", "variant")
    readonly_fields = ("updated_at",)
    show_change_link = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "items_count", "updated_at")
    list_filter = ("updated_at",)
    search_fields = ("session_key", "user__username", "user__email")
    autocomplete_fields = ("user",)
    inlines = [CartItemInline]
    ordering = ("-updated_at",)

    def items_count(self, obj: Cart):
        return obj.items.count()

    items_count.short_description = "عدد العناصر"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "variant", "quantity", "updated_at")
    search_fields = ("cart__session_key", "product__name", "variant__sku")
    autocomplete_fields = ("cart", "product", "variant")
    ordering = ("-updated_at",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product_name", "sku", "unit_price", "quantity", "line_total_display")
    readonly_fields = ("line_total_display",)
    autocomplete_fields = ("product", "variant")

    def line_total_display(self, obj: OrderItem):
        try:
            return f"{obj.line_total:.2f}"
        except Exception:
            return "—"

    line_total_display.short_description = "إجمالي السطر"


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("provider", "transaction_id", "amount", "currency", "status", "updated_at")
    readonly_fields = ("updated_at",)
    show_change_link = True


class ShipmentInline(admin.StackedInline):
    model = Shipment
    extra = 0
    fields = ("status", "carrier", "tracking_number", "shipped_at", "delivered_at", "updated_at")
    readonly_fields = ("updated_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "status", "total", "currency", "created_at", "paid_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("order_number", "user__username", "user__email", "shipping_address__full_name")
    autocomplete_fields = ("user", "shipping_address")
    ordering = ("-created_at",)

    readonly_fields = ("order_number", "created_at", "updated_at", "paid_at")
    inlines = [OrderItemInline, PaymentInline, ShipmentInline]

    actions = ("mark_paid", "mark_processing", "mark_shipped", "mark_delivered", "mark_cancelled", "recalc_totals")

    @admin.action(description="تحديد الطلبات كـ (مدفوع)")
    def mark_paid(self, request, queryset):
        now = timezone.now()
        queryset.update(status=Order.Status.PAID, paid_at=now)

    @admin.action(description="تحديد الطلبات كـ (قيد التجهيز)")
    def mark_processing(self, request, queryset):
        queryset.update(status=Order.Status.PROCESSING)

    @admin.action(description="تحديد الطلبات كـ (تم الشحن)")
    def mark_shipped(self, request, queryset):
        queryset.update(status=Order.Status.SHIPPED)

    @admin.action(description="تحديد الطلبات كـ (تم التسليم)")
    def mark_delivered(self, request, queryset):
        queryset.update(status=Order.Status.DELIVERED)

    @admin.action(description="تحديد الطلبات كـ (ملغي)")
    def mark_cancelled(self, request, queryset):
        queryset.update(status=Order.Status.CANCELLED)

    @admin.action(description="إعادة احتساب الإجماليات (subtotal/total) من عناصر الطلب")
    def recalc_totals(self, request, queryset):
        for order in queryset:
            order.recalc_totals()
            order.save(update_fields=["subtotal", "total", "updated_at"])


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product_name", "sku", "unit_price", "quantity", "created_at")
    search_fields = ("order__order_number", "product_name", "sku")
    autocomplete_fields = ("order", "product", "variant")
    ordering = ("-created_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "provider", "transaction_id", "amount", "currency", "status", "updated_at")
    list_filter = ("status", "provider", "currency")
    search_fields = ("order__order_number", "transaction_id")
    autocomplete_fields = ("order",)
    ordering = ("-updated_at",)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "carrier", "tracking_number", "updated_at")
    list_filter = ("status", "carrier")
    search_fields = ("order__order_number", "tracking_number")
    autocomplete_fields = ("order",)
    ordering = ("-updated_at",)
