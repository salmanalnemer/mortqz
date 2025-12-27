from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("home/", views.home, name="home"),
]
