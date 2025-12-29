from django.db.models import Prefetch
from django.shortcuts import render

from .models import Product, ProductImage


def catalog_home(request):
    # ✅ اعرض كل المنتجات النشطة (بدون شرط is_featured)
    products = (
        Product.objects
        .filter(is_active=True)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_primary", "sort_order", "id"),
                to_attr="prefetched_images",
            )
        )
        .order_by("-id")[:12]
    )

    return render(
        request,
        "catalog_templates/catalog_home.html",
        {
            "featured_products": products,  # نخليه نفس الاسم حتى لا نغيّر القالب
            "products_count": products.count(),
        },
    )
