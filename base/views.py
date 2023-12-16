from django.shortcuts import render, redirect
from .models import Product, Equipment, Cart, CartItem
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
    product = Product.objects.get(pk=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        cart_item.product_quantity += 1
        cart_item.save()

    return redirect('product-list')


@login_required()
def add_equipment_to_cart(request, equipment_id):
    equipment = Equipment.objects.get(pk=equipment_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, equipment=equipment)

    if not item_created:
        cart_item.equipment_quantity += 1
        cart_item.save()

    return redirect('equipment-list')


@login_required()
def remove_product_from_cart(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart = Cart.objects.get(user=request.user)
    try:
        cart_item = cart.cartitem_set.get(product=product)
        if cart_item.product_quantity >= 1:
            cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')


@login_required()
def remove_equipment_from_cart(request, equipment_id):
    equipment = Equipment.objects.get(pk=equipment_id)
    cart = Cart.objects.get(user=request.user)
    try:
        cart_item = cart.cartitem_set.get(equipment=equipment)
        if cart_item.equipment_quantity >= 1:
            cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')


@login_required()
def update_quantity(request, cart_item_id, action, item_type):
    try:
        cart_item = CartItem.objects.get(pk=cart_item_id)

        if item_type == 'product':
            quantity_attr = 'product_quantity'
        elif item_type == 'equipment':
            quantity_attr = 'equipment_quantity'
        else:
            return JsonResponse({'error': 'Invalid item type'})

        if action == 'increment':
            setattr(cart_item, quantity_attr, getattr(cart_item, quantity_attr) + 1)
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

        return JsonResponse({'success': True, 'quantity': getattr(cart_item, quantity_attr), 'totalAmount': total_amount})

    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Cart item not found'})


@login_required()
def view_cart(request):
    cart = request.user.cart
    cart_items = CartItem.objects.filter(cart=cart)

    product_total = cart_items.filter(product__isnull=False).aggregate(
        total=Sum(F('product__price') * F('product_quantity')))['total'] or 0

    equipment_total = cart_items.filter(equipment__isnull=False).aggregate(
        total=Sum(F('equipment__price') * F('equipment_quantity')))['total'] or 0

    total_amount = round(product_total + equipment_total, 2)

    return render(request, 'base/cart.html', {'cart_items': cart_items, 'total_amount': total_amount})
