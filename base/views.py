from django.shortcuts import render, redirect
from .models import Product, Cart, CartItem
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'base/index.html')


def product_list(request):
    products = Product.objects.all()
    return render(request, 'base/product_list.html', {'products': products})


@login_required()
def add_to_cart(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('product-list')


@login_required()
def remove_from_cart(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart = Cart.objects.get(user=request.user)
    try:
        cart_item = cart.cartitem_set.get(product=product)
        if cart_item.quantity >= 1:
            cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')


@login_required()
def view_cart(request):
    cart = request.user.cart
    cart_items = CartItem.objects.filter(cart=cart)
    return render(request, 'base/cart.html', {'cart_items': cart_items})
