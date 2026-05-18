from django.db import models
from django.conf import settings


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField()
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField()
    quantity = models.PositiveIntegerField(default=0)

    rental_rate = models.DecimalField(
        "Stawka najmu (za dzień)",
        max_digits=10, decimal_places=2, default=0
    )
    rental_period = models.CharField(
        "Jednostka najmu",
        max_length=10,
        choices=[('day', 'dzień'), ('week', 'tydzień'), ('month', 'miesiąc')],
        default='day'
    )
    deposit = models.DecimalField(
        "Kaucja",
        max_digits=10, decimal_places=2, default=0
    )

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


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    order_completion_date = models.DateTimeField(null=True, blank=True)

    payu_order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order #{self.id} for {self.user.username}"


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    cart_item = models.ForeignKey(CartItem, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.cart_item)


class OrderEquipment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    cart_item = models.ForeignKey(CartItem, on_delete=models.CASCADE)
    rental_rate_at_order = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deposit_at_order = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return str(self.cart_item)
