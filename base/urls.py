from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name='home'),
    path('product-list/', views.product_list, name='product-list'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('cart/', views.view_cart, name='cart'),
]
