from django.contrib import admin
from .models import Product, Equipment, Cart, CartItem, Order, OrderProduct, OrderEquipment

class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'rental_rate', 'deposit', 'quantity')


admin.site.register(Product)
admin.site.register(CartItem)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderProduct)
admin.site.register(Equipment, EquipmentAdmin)
