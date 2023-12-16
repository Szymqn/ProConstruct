from django.shortcuts import render, redirect
from .models import Product, Equipment, Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, F


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
        cart_item.product_quality += 1
        cart_item.save()

    return redirect('product-list')


@login_required()
def add_equipment_to_cart(request, equipment_id):
    equipment = Equipment.objects.get(pk=equipment_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, equipment=equipment)

    if not item_created:
        cart_item.equipment_quality += 1
        cart_item.save()

    return redirect('equipment-list')


@login_required()
def remove_product_from_cart(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart = Cart.objects.get(user=request.user)
    try:
        cart_item = cart.cartitem_set.get(product=product)
        if cart_item.product_quality >= 1:
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
        if cart_item.equipment_quality >= 1:
            cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')


@login_required()
def view_cart(request):
    cart = request.user.cart
    cart_items = CartItem.objects.filter(cart=cart)
    total_amount = cart_items.aggregate(total=Sum(F('product__price') * F('product_quality')) + Sum(F('equipment__price') * F('equipment_quality')))['total'] or 0

    return render(request, 'base/cart.html', {'cart_items': cart_items, 'total_amount': total_amount})


@login_required(login_url='login')
def increase_cart_product(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart = request.user.cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    cart_item.product_quality += 1
    cart_item.save()

    return redirect('cart')


@login_required(login_url='login')
def increase_cart_equipment(request, equipment_id):
    equipment = Equipment.objects.get(pk=equipment_id)
    cart = request.user.cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, equipment=equipment)

    cart_item.equipment_quality += 1
    cart_item.save()

    return redirect('cart')


@login_required(login_url='login')
def decrease_cart_product(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart = request.user.cart
    cart_item = cart.cartitem_set.get(product=product)

    if cart_item.product_quality > 1:
        cart_item.product_quality -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart')


@login_required(login_url='login')
def decrease_cart_equipment(request, equipment_id):
    equipment = Equipment.objects.get(pk=equipment_id)
    cart = request.user.cart
    cart_item = cart.cartitem_set.get(equipment=equipment)

    if cart_item.equipment_quality > 1:
        cart_item.equipment_quality -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart')


@login_required(login_url='login')
def fetch_cart_count(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart = request.user.cart
        cart_count = CartItem.objects.filter(cart=cart).count()
    return JsonResponse({'cart_count': cart_count})


def get_cart_count(request):
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(cart=request.user.cart)
        cart_count = cart_items.count()
    else:
        cart_count = 0
    return cart_count
