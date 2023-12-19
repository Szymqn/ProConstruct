from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Equipment, Cart, CartItem, Order, OrderProduct, OrderEquipment
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.http import JsonResponse


def index(request):
    return render(request, 'base/index.html')


def product_list(request):
    products = Product.objects.all()
    return render(request, 'base/product_list.html', {'products': products})


def equipment_list(request):
    equipments = Equipment.objects.all()
    return render(request, 'base/equipment_list.html', {'equipments': equipments})


@login_required()
def add_product_to_cart(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product does not exist")
        return redirect('product-list')

    if product.quantity == 0:
        messages.error(request, "This product is out of stock")
        return redirect('product-list')

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        if cart_item.product_quantity < product.quantity:
            cart_item.product_quantity += 1
            cart_item.save()
            product.quantity -= 1
        else:
            messages.error(request, "Cannot add more of this product to the cart")
    else:
        if cart_item.product_quantity < product.quantity:
            product.quantity -= 1

    return redirect('product-list')


@login_required()
def add_equipment_to_cart(request, equipment_id):
    try:
        equipment = Equipment.objects.get(pk=equipment_id)
    except Equipment.DoesNotExist:
        messages.error(request, "Equipment does not exist")
        return redirect('equipment-list')

    if equipment.quantity == 0:
        messages.error(request, "This equipment is out of stock")
        return redirect('equipment-list')

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, equipment=equipment)

    if not item_created:
        if cart_item.equipment_quantity < equipment.quantity:
            cart_item.equipment_quantity += 1
            cart_item.save()
            equipment.quantity -= 1
        else:
            messages.error(request, "Cannot add more of this equipment to the cart")
    else:
        if cart_item.equipment_quantity < equipment.quantity:
            equipment.quantity -= 1

    return redirect('equipment-list')


@login_required()
def remove_item_from_cart(request, item_id, model, quantity_field):
    item = get_object_or_404(model, pk=item_id)
    cart = Cart.objects.get(user=request.user)
    try:
        cart_item = cart.cartitem_set.get(**{f"{model.__name__.lower()}": item})
        if getattr(cart_item, quantity_field) >= 1:
            cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')


@login_required()
def remove_product_from_cart(request, product_id):
    return remove_item_from_cart(request, product_id, Product, 'product_quantity')


@login_required()
def remove_equipment_from_cart(request, equipment_id):
    return remove_item_from_cart(request, equipment_id, Equipment, 'equipment_quantity')


@login_required()
def update_quantity(request, cart_item_id, action, item_type):
    try:
        cart_item = CartItem.objects.get(pk=cart_item_id)

        if item_type not in ['product', 'equipment']:
            return JsonResponse({'error': 'Invalid item type'})

        quantity_attr = f'{item_type}_quantity'

        if action == 'increment':
            if quantity_attr == "product_quantity":
                if getattr(cart_item, quantity_attr) < cart_item.product.quantity:
                    setattr(cart_item, quantity_attr, getattr(cart_item, quantity_attr) + 1)
            elif quantity_attr == "equipment_quantity":
                if getattr(cart_item, quantity_attr) < cart_item.equipment.quantity:
                    setattr(cart_item, quantity_attr, getattr(cart_item, quantity_attr) + 1)
            else:
                return JsonResponse({'error': 'Cannot add more of this item to the cart'})
        elif action == 'decrement' and getattr(cart_item, quantity_attr) > 1:
            setattr(cart_item, quantity_attr, getattr(cart_item, quantity_attr) - 1)
        else:
            return JsonResponse({'error': 'Invalid action'})

        cart_item.save()

        product_total = CartItem.objects.filter(product__isnull=False).aggregate(
            total=Sum(F('product__price') * F('product_quantity')))['total'] or 0

        equipment_total = CartItem.objects.filter(equipment__isnull=False).aggregate(
            total=Sum(F('equipment__price') * F('equipment_quantity')))['total'] or 0

        total_amount = round(product_total + equipment_total, 2)

        return JsonResponse(
            {'success': True, 'quantity': getattr(cart_item, quantity_attr), 'totalAmount': total_amount})

    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Cart item not found'})


def calculate_total_amount(request):
    cart = request.user.cart
    cart_items = CartItem.objects.filter(cart=cart)

    product_total = cart_items.filter(product__isnull=False).aggregate(
        total=Sum(F('product__price') * F('product_quantity')))['total'] or 0

    equipment_total = cart_items.filter(equipment__isnull=False).aggregate(
        total=Sum(F('equipment__price') * F('equipment_quantity')))['total'] or 0

    return cart_items, round(product_total + equipment_total, 2)


@login_required()
def view_cart(request):
    cart_items, total_amount = calculate_total_amount(request)

    return render(request, 'base/cart.html', {'cart_items': cart_items, 'total_amount': total_amount})


@login_required
@transaction.atomic
def checkout(request):
    cart_items, total_amount = calculate_total_amount(request)

    order = Order.objects.create(user=request.user)
    order_products = []
    order_equipments = []

    for cart_item in cart_items:
        if cart_item.product:
            order_product = OrderProduct.objects.create(order=order, cart_item=cart_item)
            order_products.append([order_product.cart_item.product.name, cart_item.product_quantity])
        elif cart_item.equipment:
            order_equipment = OrderEquipment.objects.create(order=order, cart_item=cart_item)
            order_equipments.append([order_equipment.cart_item.equipment.name, cart_item.equipment_quantity])

    return render(request, 'base/checkout.html', {'order': order, 'order_products': order_products, 'order_equipments': order_equipments, 'total_amount': total_amount})
