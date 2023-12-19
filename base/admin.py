from django.contrib import admin
from .models import Product, Equipment, Cart, CartItem, Order, OrderProduct, OrderEquipment

admin.site.register(Product)
admin.site.register(Equipment)
admin.site.register(CartItem)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderProduct)
admin.site.register(OrderEquipment)
