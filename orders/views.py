from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse, HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST

from catalog.models import Product  # ✅ مهم: لأن المنتجات عندك داخل catalog
from .models import Cart, CartItem


def home(request: HttpRequest):
    """
    صفحة المتجر (الرئيسية) مع المنتجات المميزة.
    ملاحظة: غيّر اسم القالب إذا عندك قالب مختلف.
    """
    featured_products = (
        Product.objects.filter(is_active=True)
        .order_by("-is_featured", "-updated_at", "-id")[:12]
    )
    return render(request, "catalog_home.html", {"featured_products": featured_products})


def _get_or_create_cart(request: HttpRequest) -> Cart:
    """
    يرجّع سلة للمستخدم المسجل أو للزائر عبر session_key.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    cart, _ = Cart.objects.get_or_create(user=None, session_key=session_key)
    return cart

  # وظائف مساعدة داخلية
def _cart_items_count(cart: Cart) -> int:
    """
    مجموع الكميات في السلة (quantity).
    """
    return sum(cart.items.values_list("quantity", flat=True))


def _get_stock_info(obj) -> tuple[bool, int]:
    """
    يرجّع (track_inventory, stock_quantity) لكائن Product أو ProductVariant.
    """
    track = bool(getattr(obj, "track_inventory", False))
    stock = int(getattr(obj, "stock_quantity", 0) or 0)
    return track, stock


def _item_unit_price_and_currency(item: CartItem) -> tuple[Decimal, str]:
    # تحديد سعر الوحدة والعملة للعنصر
    if item.variant_id:
        return (item.variant.price or Decimal("0.00"), item.variant.currency or "SAR")
    #   تحديد سعر الوحدة والعملة للعنصر
    if item.product_id:
    #   تحديد سعر الوحدة والعملة للعنصر
        return (item.product.price or Decimal("0.00"), item.product.currency or "SAR")
    return (Decimal("0.00"), "SAR")


def _item_title(item: CartItem) -> str:
    # تحديد عنوان العنصر في السلة
    if item.variant_id:
        v = item.variant
        label = v.title or v.sku or ""
        #   إرجاع اسم المنتج مع تسمية المتغير إذا وجدت
        return f"{v.product.name} - {label}" if label else v.product.name
    if item.product_id:
        return item.product.name
    return "عنصر"


def _item_image_url(item: CartItem) -> str:
    if item.variant_id:
        return item.variant.product.primary_image_url
    if item.product_id:
        return item.product.primary_image_url
    return ""


def _calc_cart_subtotal(cart: Cart) -> tuple[Decimal, str]:
    # حساب المجموع الفرعي للسلة
    items_qs = cart.items.select_related("product", "variant", "variant__product").all()
    subtotal = Decimal("0.00")
    currency = "SAR"
    for it in items_qs:
        unit_price, cur = _item_unit_price_and_currency(it)
        subtotal += (unit_price * it.quantity)
        if cur:
            currency = cur
    return subtotal, currency


@require_POST
@transaction.atomic
def cart_add(request: HttpRequest):
    product_id = (request.POST.get("product_id") or "").strip()
    variant_id = (request.POST.get("variant_id") or "").strip()
    qty_raw = (request.POST.get("quantity") or "1").strip()

    try:
        quantity = int(qty_raw)
    except ValueError:
        return JsonResponse({"ok": False, "error": "قيمة الكمية غير صحيحة."}, status=400)

    if quantity < 1 or quantity > 999:
        return JsonResponse({"ok": False, "error": "الكمية يجب أن تكون بين 1 و 999."}, status=400)

    if bool(product_id) == bool(variant_id):
        return JsonResponse({"ok": False, "error": "أرسل product_id أو variant_id فقط."}, status=400)

    cart = _get_or_create_cart(request)
    Cart.objects.select_for_update().filter(pk=cart.pk).exists()

    ProductModel = CartItem._meta.get_field("product").remote_field.model
    VariantModel = CartItem._meta.get_field("variant").remote_field.model

    if product_id:
        product = get_object_or_404(ProductModel, pk=product_id)

        existing_qty = (
            CartItem.objects.filter(cart=cart, product=product, variant__isnull=True)
            .values_list("quantity", flat=True)
            .first()
        ) or 0

        track, stock = _get_stock_info(product)
        requested_total = existing_qty + quantity

        if track and stock <= 0:
            return JsonResponse({"ok": False, "error": "المنتج غير متوفر حالياً."}, status=400)
        if track and requested_total > stock:
            return JsonResponse({"ok": False, "error": "الكمية المطلوبة غير متوفرة بالمخزون."}, status=400)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=None,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity = requested_total
            item.save(update_fields=["quantity", "updated_at"])

    else:
        variant = get_object_or_404(VariantModel, pk=variant_id)

        existing_qty = (
            CartItem.objects.filter(cart=cart, variant=variant, product__isnull=True)
            .values_list("quantity", flat=True)
            .first()
        ) or 0

        track, stock = _get_stock_info(variant)
        requested_total = existing_qty + quantity

        if track and stock <= 0:
            return JsonResponse({"ok": False, "error": "المتغير غير متوفر حالياً."}, status=400)
        if track and requested_total > stock:
            return JsonResponse({"ok": False, "error": "الكمية المطلوبة غير متوفرة بالمخزون."}, status=400)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=None,
            variant=variant,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity = requested_total
            item.save(update_fields=["quantity", "updated_at"])

    return JsonResponse({"ok": True, "cart_count": _cart_items_count(cart)})


def cart_summary(request: HttpRequest):
    cart = _get_or_create_cart(request)
    return JsonResponse({"ok": True, "cart_count": _cart_items_count(cart)})


@transaction.atomic
def cart_detail(request: HttpRequest):
    cart = _get_or_create_cart(request)

    items_qs = (
        cart.items.select_related("product", "variant", "variant__product")
        .all()
        .order_by("-updated_at", "-created_at")
    )

    rows: list[dict] = []
    subtotal = Decimal("0.00")
    currency = "SAR"

    for it in items_qs:
        unit_price, cur = _item_unit_price_and_currency(it)
        line_total = unit_price * it.quantity
        subtotal += line_total
        if cur:
            currency = cur

        rows.append(
            {
                "id": it.id,
                "title": _item_title(it),
                "image_url": _item_image_url(it),
                "quantity": it.quantity,
                "unit_price": unit_price,
                "line_total": line_total,
                "sku": (it.variant.sku if it.variant_id else ""),
                "is_variant": bool(it.variant_id),
            }
        )

    context = {
        "cart": cart,
        "items": rows,
        "subtotal": subtotal,
        "currency": currency,
        "cart_count": _cart_items_count(cart),
    }
    return render(request, "orders_templates/cart_detail.html", context)


@require_POST
@transaction.atomic
def cart_update(request: HttpRequest, item_id: int):
    """
    ✅ تحديث الكمية مع معالجة المخزون بشكل ذكي:
    - إذا كانت الكمية المطلوبة أكبر من المتاح:
      نضبطها تلقائياً للحد المتاح ونرجع رسالة (بدل ok:false).
    - إذا المخزون = 0:
      نرجع خطأ واضح (out_of_stock) لكي تحذف العنصر.
    """
    cart = _get_or_create_cart(request)
    Cart.objects.select_for_update().filter(pk=cart.pk).exists()

    item = get_object_or_404(
        CartItem.objects.select_related("product", "variant", "variant__product"),
        pk=item_id,
        cart=cart,
    )

    qty_raw = (request.POST.get("quantity") or "").strip()
    try:
        requested_qty = int(qty_raw)
    except ValueError:
        return JsonResponse({"ok": False, "error": "قيمة الكمية غير صحيحة."}, status=400)

    if requested_qty < 1 or requested_qty > 999:
        return JsonResponse({"ok": False, "error": "الكمية يجب أن تكون بين 1 و 999."}, status=400)

    # تحديد كائن المخزون
    stock_obj = item.variant if item.variant_id else item.product
    track, stock = _get_stock_info(stock_obj) if stock_obj else (False, 0)

    adjusted = False
    final_qty = requested_qty

    if track:
        if stock <= 0:
            msg = "هذا المنتج أصبح غير متوفر. فضلاً احذفه من السلة."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "error": msg, "out_of_stock": True}, status=400)
            return redirect("orders:cart_detail")

        if requested_qty > stock:
            final_qty = stock
            adjusted = True

    item.quantity = final_qty
    item.save(update_fields=["quantity", "updated_at"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cart_count = _cart_items_count(cart)
        subtotal, currency = _calc_cart_subtotal(cart)
        unit_price, _cur = _item_unit_price_and_currency(item)
        line_total = unit_price * item.quantity

        payload = {
            "ok": True,
            "cart_count": cart_count,
            "subtotal": str(subtotal),
            "currency": currency,
            "item": {"id": item.id, "quantity": item.quantity, "line_total": str(line_total)},
        }
        if adjusted:
            payload["adjusted"] = True
            payload["message"] = f"تم تعديل الكمية إلى الحد المتاح ({final_qty})."
        return JsonResponse(payload)

    return redirect("orders:cart_detail")


@require_POST
@transaction.atomic
def cart_remove(request: HttpRequest, item_id: int):
    cart = _get_or_create_cart(request)
    Cart.objects.select_for_update().filter(pk=cart.pk).exists()

    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        subtotal, currency = _calc_cart_subtotal(cart)
        return JsonResponse(
            {
                "ok": True,
                "cart_count": _cart_items_count(cart),
                "subtotal": str(subtotal),
                "currency": currency,
            }
        )

    return redirect("orders:cart_detail")
