from django.contrib import admin
from .models import Product, Equipment, Cart, CartItem

admin.site.register(Product)
admin.site.register(Equipment)
admin.site.register(CartItem)
admin.site.register(Cart)
