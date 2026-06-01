import os

from django.utils import timezone
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Equipment, Cart, CartItem, Order, OrderProduct, OrderEquipment
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.http import JsonResponse
from .stripe_service import StripeService
from datetime import datetime

def index(request):
    return render(request, 'base/homepage.html')


def product_list(request):
    products = Product.objects.all()
    return render(request, 'base/product_list.html', {'products': products})

def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'base/product_details.html', {'product': product})

def equipment_list(request):
    equipments = Equipment.objects.all()
    return render(request, 'base/equipment_list.html', {'equipments': equipments})

def equipment_details(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)
    return render(request, 'base/equipment_details.html', {'equipment': equipment})

def regulations(request):
    return render(request, 'base/regulations.html')


@login_required()
def add_product_to_cart(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Produkt nie istnieje")
        return redirect('product-list')

    if product.quantity == 0:
        messages.error(request, "Brak produktu na stanie")
        return redirect('product-list')

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        if cart_item.product_quantity < product.quantity:
            cart_item.product_quantity += 1
            cart_item.save()
            product.quantity -= 1
        else:
            messages.error(request, "Nie można dodać więcej tego produktu do koszyka")
    else:
        if cart_item.product_quantity < product.quantity:
            product.quantity -= 1

    return redirect('product-list')


@login_required()
def add_equipment_to_cart(request, equipment_id):
    if request.method != "POST":
        return redirect('equipment-list')
        
    rent_start_date_str = request.POST.get('start_date')
    rent_end_date_str = request.POST.get('end_date')

    if not rent_start_date_str or not rent_end_date_str:
        messages.error(request, "Musisz wybrać daty wynajmu.")
        return redirect('equipment-details', equipment_id=equipment_id)
    
    # Konwersja tekstu na obiekty daty i sprawdzenie ich kolejności
    try:
        # Zakładamy format YYYY-MM-DD (standardowy dla <input type="date">)
        rent_start_date = datetime.strptime(rent_start_date_str, "%Y-%m-%d").date()
        rent_end_date = datetime.strptime(rent_end_date_str, "%Y-%m-%d").date()
        
        if rent_start_date > rent_end_date:
            messages.error(request, "Data początkowa nie może być późniejsza niż data końcowa.")
            return redirect('equipment-details', equipment_id=equipment_id)
            
    except ValueError:
        messages.error(request, "Nieprawidłowy format daty.")
        return redirect('equipment-details', equipment_id=equipment_id)
    

    try:
        equipment = Equipment.objects.get(pk=equipment_id)
    except Equipment.DoesNotExist:
        messages.error(request, "Narzędzie nie istnieje")
        return redirect('equipment-list')

    if equipment.quantity == 0:
        messages.error(request, "Brak narzędzia na stanie")
        return redirect('equipment-list')

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart, 
        equipment=equipment,
        rent_start_date=rent_start_date,
        rent_end_date=rent_end_date
    )

    if not item_created:
        if cart_item.equipment_quantity < equipment.quantity:
            cart_item.equipment_quantity += 1
            cart_item.save()
            equipment.quantity -= 1
            equipment.save()
        else:
            messages.error(request, "Nie można dodać więcej tego narzędzia do koszyka")
    else:
        if cart_item.equipment_quantity < equipment.quantity:
            equipment.quantity -= 1
            equipment.save()

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
        cart_item = CartItem.objects.select_related('product', 'equipment').get(pk=cart_item_id)

        if item_type not in ['product', 'equipment']:
            return JsonResponse({'error': 'Invalid item type'})

        quantity_attr = f'{item_type}_quantity'

        if action == 'increment':
            if quantity_attr == "product_quantity":
                if getattr(cart_item, quantity_attr) < cart_item.product.quantity:
                    setattr(cart_item, quantity_attr, getattr(cart_item, quantity_attr) + 1)
                else:
                    return JsonResponse({'error': 'Brak wystarczającej ilości produktu na stanie'})
            elif quantity_attr == "equipment_quantity":
                if getattr(cart_item, quantity_attr) < cart_item.equipment.quantity:
                    setattr(cart_item, quantity_attr, getattr(cart_item, quantity_attr) + 1)
                else:
                    return JsonResponse({'error': 'Brak wystarczającej ilości narzędzi na stanie'})
        elif action == 'decrement' and getattr(cart_item, quantity_attr) > 1:
            setattr(cart_item, quantity_attr, getattr(cart_item, quantity_attr) - 1)
        else:
            return JsonResponse({'error': 'Invalid action or limit reached'})

        cart_item.save()

        # Wywołujemy funkcję liczącą koszty, aby uniknąć duplikacji kodu
        # i uwzględnić nową logikę liczenia dni dla sprzętu
        _, total_amount = calculate_total_amount(request)

        return JsonResponse({
            'success': True, 
            'quantity': getattr(cart_item, quantity_attr), 
            'totalAmount': total_amount
        })

    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Cart item not found'})
    

def calculate_total_amount(request):
    cart = request.user.cart
    cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'equipment')

    product_total = cart_items.filter(product__isnull=False).aggregate(
        total=Sum(F('product__price') * F('product_quantity'))
    )['total'] or 0

    equipment_total = 0
    # Obliczamy koszty wynajmu z uwzględnieniem dni
    for item in cart_items.filter(equipment__isnull=False):
        days = 1
        if item.rent_start_date and item.rent_end_date:
            delta = item.rent_end_date - item.rent_start_date
            days = delta.days if delta.days > 0 else 1 # Zabezpieczenie przed ujemnymi datami / 0 dni

        rental_cost = item.equipment.rental_rate * item.equipment_quantity * days
        deposit_cost = item.equipment.deposit * item.equipment_quantity
        equipment_total += (rental_cost + deposit_cost)

    return cart_items, round(product_total + equipment_total, 2)


@login_required()
def view_cart(request):
    cart_items, total_amount = calculate_total_amount(request)

    stripe_public_key = os.environ.get('STRIPE_PUBLIC_KEY', '')

    return render(request, 'base/cart.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'stripe_public_key': stripe_public_key
    })

@login_required
@transaction.atomic
def checkout(request):
    cart_items, total_amount = calculate_total_amount(request)

    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        payment_status='pending'
    )
    order_products = []
    order_equipments = []

    for cart_item in cart_items:
        if cart_item.product:
            order_product = OrderProduct.objects.create(order=order, cart_item=cart_item)
            order_products.append([order_product.cart_item.product.name, cart_item.product_quantity])

            product = cart_item.product
            product.quantity -= cart_item.product_quantity
            product.save()
        elif cart_item.equipment:
            order_equipment = OrderEquipment.objects.create(
                order=order,
                cart_item=cart_item,
                rental_rate_at_order=cart_item.equipment.rental_rate,
                deposit_at_order=cart_item.equipment.deposit,
            )

            order_equipments.append([order_equipment.cart_item.equipment.name, cart_item.equipment_quantity])

            equipment = cart_item.equipment
            equipment.quantity -= cart_item.equipment_quantity
            equipment.save()

    return render(request, 'base/checkout.html', {'order': order, 'order_products': order_products, 'order_equipments': order_equipments, 'total_amount': total_amount})


@login_required()
def initiate_payment(request, order_id):
    """Inicjuj płatność Stripe"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('home')

    stripe_service = StripeService()

    success_url = request.build_absolute_uri(f'/payment-success/{order_id}/')
    cancel_url = request.build_absolute_uri(f'/payment-cancel/{order_id}/')

    result = stripe_service.create_checkout_session(
        order_id=order.id,
        amount=order.total_amount,
        customer_email=order.user.email,
        success_url=request.build_absolute_uri(f"/payment-success/{order.id}/"),
        cancel_url=request.build_absolute_uri(f"/payment-cancel/{order.id}/"),
    )

    if result["status"] == "success":
        order.payu_order_id = result["session_id"]
        order.save()
        return redirect(result["checkout_url"])

    messages.error(request, result.get("message", "Payment initialization failed"))
    return redirect("cart")


@login_required()
def payment_success(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)

        # Stripe dodaje session_id w success_url
        session_id = request.GET.get("session_id") or order.payu_order_id
        if not session_id:
            messages.error(request, "Brak session_id Stripe.")
            return redirect("cart")

        stripe_service = StripeService()
        result = stripe_service.retrieve_session(session_id)

        if result["status"] != "success":
            messages.error(request, f"Stripe verify error: {result.get('message')}")
            return redirect("cart")

        session = result["session"]
        if session.payment_status == "paid":
            order.payment_status = "completed"
            order.order_completion_date = timezone.now()
            order.save()

            # wyczyść koszyk użytkownika
            try:
                request.user.cart.cartitem_set.all().delete()
            except Exception:
                pass

            messages.success(request, "Payment successful!")
        else:
            messages.warning(request, f"Payment status: {session.payment_status}")

        return redirect("home")
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect("home")


@login_required()
def payment_cancel(request, order_id):
    """Anulowanie płatności"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        order.payment_status = 'cancelled'
        order.save()
        messages.warning(request, "Payment was cancelled")
        return render(request, 'base/payment_cancel.html', {'order': order})
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('home')
