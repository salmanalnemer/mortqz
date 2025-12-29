from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = "orders"


def orders_home(request):
    # ✅ الصفحة الرئيسية الفعلية عندك هي "/"
    return redirect("/")


urlpatterns = [
    # ✅ هذا هو الإصلاح: صار عندنا name="home" عشان {% url 'orders:home' %} يشتغل
    path("", orders_home, name="home"),

    # (اختياري) مسار بديل لو كنت تستخدمه سابقًا
    path("index/", orders_home, name="index"),

    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/summary/", views.cart_summary, name="cart_summary"),

    path("cart/item/<int:item_id>/update/", views.cart_update, name="cart_update"),
    path("cart/item/<int:item_id>/remove/", views.cart_remove, name="cart_remove"),
]
