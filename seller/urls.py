from django.urls import path

from . import views

urlpatterns = [
    path('orders_manage/', views.orders_manage, name='orders_manage'),
]
