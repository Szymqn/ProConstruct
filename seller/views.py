from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from base.models import Order, OrderProduct, OrderEquipment


@login_required()
@user_passes_test(lambda u: u.is_staff)
def orders_manage(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id_to_delete')
        if order_id:
            try:
                order_to_delete = Order.objects.get(pk=order_id)
                order_to_delete.delete()
                return redirect('orders_manage')
            except Order.DoesNotExist:
                pass

    orders = Order.objects.all()

    order_data = []

    for order in orders:
        order_products = OrderProduct.objects.filter(order=order)
        order_equipments = OrderEquipment.objects.filter(order=order)

        total_amount_products = sum(product.cart_item.product.price * product.cart_item.product_quantity for product in order_products)
        total_amount_equipments = sum(equipment.cart_item.equipment.price * equipment.cart_item.equipment_quantity for equipment in order_equipments)

        total_amount = total_amount_products + total_amount_equipments

        order_data.append({
            'order': order,
            'order_products': order_products,
            'order_equipments': order_equipments,
            'total_amount': total_amount
        })

    return render(request, 'seller/orders_manage.html', {'order_data': order_data})
