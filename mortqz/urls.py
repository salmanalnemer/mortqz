from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

# ✅ استيراد view الرئيسية (تأكد أن views.py موجود بنفس مجلد هذا urls.py)
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ الصفحة الرئيسية عند فتح الموقع
    path('', views.home, name='home'),

    # Apps routes
    path('accounts/', include('accounts.urls')),
    path('shop/', include('catalog.urls')),

    # ✅ نقل السلة/الطلب/الدفع إلى /orders/ بدل الجذر
    path('orders/', include('orders.urls')),
]

# ✅ لخدمة ملفات media أثناء التطوير فقط
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
