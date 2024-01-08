from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .forms import CustomUserCreationForm, LoginForm
from base.models import Order, OrderProduct, OrderEquipment


def user_signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/signup.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def user_details(request):
    user = request.user
    return render(request, 'users/user_details.html', {'user': user})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'users/password_change.html', {'form': form})


@login_required
def check_orders(request):
    orders = Order.objects.filter(user=request.user)

    order_data = []

    for order in orders:
        order_products = OrderProduct.objects.filter(order=order)
        order_equipments = OrderEquipment.objects.filter(order=order)

        total_amount_products = sum(
            product.cart_item.product.price * product.cart_item.product_quantity for product in order_products)
        total_amount_equipments = sum(
            equipment.cart_item.equipment.price * equipment.cart_item.equipment_quantity for equipment in
            order_equipments)

        total_amount = total_amount_products + total_amount_equipments

        order_data.append({
            'order': order,
            'order_products': order_products,
            'order_equipments': order_equipments,
            'total_amount': total_amount
        })

    return render(request, 'users/check_orders.html', {'order_data': order_data})
