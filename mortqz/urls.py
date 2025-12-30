from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("sansmanger/", admin.site.urls),

    # ✅ الصفحة الرئيسية (منتجات مميزة / واجهة المتجر)
    path("", include(("catalog.urls", "catalog"), namespace="catalog")),

    # التطبيقات
    path("accounts/", include("accounts.urls")),
    path("orders/", include("orders.urls")),
]

# ملفات الميديا (للتطوير فقط)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
