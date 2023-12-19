from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name='home'),
    path('product-list/', views.product_list, name='product-list'),
    path('add-product-to-cart/<int:product_id>/', views.add_product_to_cart, name='add-product-to-cart'),
    path('remove-product-from-cart/<int:product_id>/', views.remove_product_from_cart, name='remove-product-from-cart'),
    path('equipment-list/', views.equipment_list, name='equipment-list'),
    path('add-equipment-to-cart/<int:equipment_id>/', views.add_equipment_to_cart, name='add-equipment-to-cart'),
    path('remove-equipmet-from-cart/<int:equipment_id>/', views.remove_equipment_from_cart, name='remove-equipment-from-cart'),
    path('cart/', views.view_cart, name='cart'),
    path('update-quantity/<int:cart_item_id>/<str:action>/<str:item_type>/', views.update_quantity, name='update-quantity'),
    path('checkout/', views.checkout, name='checkout'),
]
