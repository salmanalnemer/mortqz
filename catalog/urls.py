from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    # الصفحة الرئيسية للمتجر
    path("", views.catalog_home, name="home"),
]
