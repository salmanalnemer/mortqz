from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Apps routes
    path('accounts/', include('accounts.urls')),
    path('shop/', include('catalog.urls')),
    path('', include('orders.urls')),  # السلة/الطلب/الدفع على الجذر (اختياري)
]
