from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Prefetch
from base.models import Order, OrderProduct, OrderEquipment
import csv
from datetime import datetime, timedelta, time
import calendar


class Command(BaseCommand):
    help = 'Generate a CSV sales summary for completed orders in a given date range (defaults to last 30 days)'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, help='Start date YYYY-MM-DD')
        parser.add_argument('--end', type=str, help='End date YYYY-MM-DD')
        parser.add_argument('--output', type=str, help='Output CSV file path (defaults to stdout)')

    def handle(self, *args, **options):
        # determine date range
        end = None
        start = None
        # Parse user-provided dates (YYYY-MM-DD) and make them timezone-aware.
        if options.get('end'):
            try:
                end_date = datetime.strptime(options['end'], "%Y-%m-%d").date()
            except ValueError:
                # attempt to auto-correct day overflow (e.g., 2026-06-31 -> 2026-06-30)
                try:
                    y, m, d = map(int, options['end'].split('-'))
                    max_day = calendar.monthrange(y, m)[1]
                    if d > max_day:
                        corrected = f"{y:04d}-{m:02d}-{max_day:02d}"
                        self.stdout.write(self.style.WARNING(f"End date {options['end']} is invalid, auto-correcting to {corrected}"))
                        end_date = datetime.strptime(corrected, "%Y-%m-%d").date()
                    else:
                        raise CommandError('Invalid end date format, use YYYY-MM-DD')
                except Exception:
                    raise CommandError('Invalid end date format, use YYYY-MM-DD')
            # end of day to make the range inclusive
            end = datetime.combine(end_date, time.max)
            end = timezone.make_aware(end, timezone.get_current_timezone())

        if options.get('start'):
            try:
                start_date = datetime.strptime(options['start'], "%Y-%m-%d").date()
            except ValueError:
                # attempt to auto-correct day overflow
                try:
                    y, m, d = map(int, options['start'].split('-'))
                    max_day = calendar.monthrange(y, m)[1]
                    if d > max_day:
                        corrected = f"{y:04d}-{m:02d}-{max_day:02d}"
                        self.stdout.write(self.style.WARNING(f"Start date {options['start']} is invalid, auto-correcting to {corrected}"))
                        start_date = datetime.strptime(corrected, "%Y-%m-%d").date()
                    else:
                        raise CommandError('Invalid start date format, use YYYY-MM-DD')
                except Exception:
                    raise CommandError('Invalid start date format, use YYYY-MM-DD')
            # start of day
            start = datetime.combine(start_date, time.min)
            start = timezone.make_aware(start, timezone.get_current_timezone())

        if not end:
            end = timezone.now()

        if not start:
            # default to last 30 days
            start = end - timedelta(days=30)

        # fetch completed orders in range, prefetch related items for efficiency
        order_products_qs = OrderProduct.objects.select_related('cart_item__product')
        order_equipments_qs = OrderEquipment.objects.select_related('cart_item__equipment')

        orders = Order.objects.filter(payment_status='completed', order_completion_date__range=(start, end)).prefetch_related(
            Prefetch('orderproduct_set', queryset=order_products_qs, to_attr='prefetched_products'),
            Prefetch('orderequipment_set', queryset=order_equipments_qs, to_attr='prefetched_equipments')
        ).select_related('user')

        rows = []
        total_revenue = 0
        total_orders = orders.count()

        for order in orders:
            products = []
            equipments = []
            products_total = 0
            equipments_total = 0

            for op in getattr(order, 'prefetched_products', []):
                p = op.cart_item.product
                qty = op.cart_item.product_quantity
                products.append(f"{p.name} x{qty}")
                products_total += float(p.price) * qty

            for oe in getattr(order, 'prefetched_equipments', []):
                e = oe.cart_item.equipment
                qty = oe.cart_item.equipment_quantity
                equipments.append(f"{e.name} x{qty}")
                # use rental rate at order if present else current price
                rate = oe.rental_rate_at_order if oe.rental_rate_at_order is not None else float(e.rental_rate)
                equipments_total += float(rate) * qty

            order_revenue = float(order.total_amount) if order.total_amount is not None else (products_total + equipments_total)
            total_revenue += order_revenue

            rows.append({
                'order_id': order.id,
                'user': str(order.user),
                'date': order.order_completion_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_completion_date else '',
                'order_revenue': order_revenue,
                'products': '; '.join(products),
                'equipments': '; '.join(equipments)
            })

        # write CSV
        fieldnames = ['order_id', 'user', 'date', 'order_revenue', 'products', 'equipments']

        output_path = options.get('output')
        if output_path:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            self.stdout.write(self.style.SUCCESS(f'Wrote {len(rows)} orders to {output_path}'))
        else:
            writer = csv.DictWriter(self.stdout, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        # summary
        self.stdout.write(self.style.SUCCESS(f'Total orders: {total_orders}'))
        self.stdout.write(self.style.SUCCESS(f'Total revenue: {total_revenue:.2f}'))
