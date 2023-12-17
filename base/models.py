from django.db import models
from django.conf import settings


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField()
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField()
    quantity = models.PositiveIntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name


class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True)
    product_quantity = models.PositiveIntegerField(default=1)
    equipment_quantity = models.PositiveIntegerField(default=1)


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField(Product, through='CartItem')
    equipments = models.ManyToManyField(Equipment, through='CartItem')

    def __str__(self):
        return f"Cart for {self.user.username}"
