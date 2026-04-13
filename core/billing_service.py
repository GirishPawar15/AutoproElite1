"""
Spare Parts Billing Service
Handles all billing operations including stock management
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import SparePart, Order, OrderItem, SalesReport, StockTransaction
from .ebill_generator import generate_ebill_pdf
from .email_utils import send_ebill_email


class BillingService:
    """Service class for spare parts billing operations"""
    
    @staticmethod
    def create_spare_parts_bill(items, customer_data, payment_method='cash', apply_gst=True):
        """
        Create a bill for spare parts purchase
        
        Args:
            items: List of dicts with 'sku', 'quantity'
            customer_data: Dict with customer info
            payment_method: Payment method (cash, card, upi, etc.)
            apply_gst: Whether to apply GST (18%)
        
        Returns:
            Order object or None if failed
        """
        try:
            with transaction.atomic():
                # Calculate totals
                subtotal = Decimal('0.00')
                order_items_data = []
                
                # Validate and prepare items
                for item in items:
                    spare_part = SparePart.objects.get(sku=item['sku'], is_active=True)
                    quantity = int(item['quantity'])
                    
                    # Check stock availability
                    if spare_part.stock < quantity:
                        raise ValueError(f"Insufficient stock for {spare_part.name}. Available: {spare_part.stock}")
                    
                    item_total = spare_part.price * quantity
                    subtotal += item_total
                    
                    order_items_data.append({
                        'spare_part': spare_part,
                        'quantity': quantity,
                        'price': spare_part.price,
                        'total': item_total
                    })
                
                # Calculate tax and total
                tax_amount = (subtotal * Decimal('0.18')) if apply_gst else Decimal('0.00')
                delivery_charge = Decimal('0.00')  # No delivery for in-store purchase
                total_amount = subtotal + tax_amount + delivery_charge
                
                # Create order
                order = Order.objects.create(
                    user=customer_data.get('user'),
                    order_type='spare',
                    status='completed',  # Immediate completion for POS
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    delivery_charge=delivery_charge,
                    total_amount=total_amount,
                    customer_name=customer_data.get('name', ''),
                    customer_email=customer_data.get('email', ''),
                    customer_phone=customer_data.get('phone', ''),
                    payment_method=payment_method,
                )
                
                # Create order items and reduce stock
                for item_data in order_items_data:
                    spare_part = item_data['spare_part']
                    quantity = item_data['quantity']
                    
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product_id=spare_part.sku,
                        name=spare_part.name,
                        price=item_data['price'],
                        quantity=quantity,
                        image_url=spare_part.image_url or '',
                    )
                    
                    # Reduce stock
                    previous_stock = spare_part.stock
                    spare_part.stock -= quantity
                    spare_part.save()
                    
                    # Record stock transaction
                    StockTransaction.objects.create(
                        spare_part=spare_part,
                        transaction_type='sale',
                        quantity=-quantity,
                        previous_stock=previous_stock,
                        new_stock=spare_part.stock,
                        order=order,
                        notes=f"Sold via POS - Order #{order.id}",
                        created_by=customer_data.get('user'),
                    )
                
                # Generate bill number
                order.bill_number = BillingService.generate_bill_number()
                order.bill_date = timezone.now()
                order.save()
                
                # Generate PDF
                pdf_path = generate_ebill_pdf(order)
                if pdf_path:
                    order.bill_pdf_path = pdf_path
                    order.save()
                
                # Send email if email provided
                if customer_data.get('email'):
                    send_ebill_email(order, pdf_path)
                
                # Update sales report
                BillingService.update_sales_report(order)
                
                return order
                
        except Exception as e:
            print(f"Error creating bill: {str(e)}")
            return None
    
    @staticmethod
    def generate_bill_number():
        """Generate unique bill number"""
        from datetime import datetime
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        # Count today's orders
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        count = Order.objects.filter(
            created_at__gte=today_start,
            order_type='spare'
        ).count() + 1
        
        return f"APE-{date_str}-{count:06d}"
    
    @staticmethod
    def update_sales_report(order):
        """Update daily sales report"""
        report_date = order.created_at.date()
        
        report, created = SalesReport.objects.get_or_create(
            report_date=report_date,
            defaults={
                'total_sales': Decimal('0.00'),
                'total_orders': 0,
                'total_items_sold': 0,
            }
        )
        
        report.total_sales += order.total_amount
        report.total_orders += 1
        report.total_items_sold += order.items.count()
        report.save()
    
    @staticmethod
    def get_low_stock_items(threshold=10):
        """Get spare parts with low stock"""
        return SparePart.objects.filter(
            stock__lte=threshold,
            is_active=True
        ).order_by('stock')
    
    @staticmethod
    def get_sales_summary(start_date, end_date):
        """Get sales summary for date range"""
        orders = Order.objects.filter(
            order_type='spare',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        total_sales = sum(order.total_amount for order in orders)
        total_orders = orders.count()
        
        return {
            'total_sales': total_sales,
            'total_orders': total_orders,
            'average_order_value': total_sales / total_orders if total_orders > 0 else 0,
        }
    
    @staticmethod
    def get_top_selling_products(limit=10, days=30):
        """Get top selling spare parts"""
        from django.db.models import Sum, Count
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        top_products = OrderItem.objects.filter(
            order__order_type='spare',
            order__created_at__gte=start_date
        ).values('product_id', 'name').annotate(
            total_quantity=Sum('quantity'),
            total_orders=Count('order', distinct=True)
        ).order_by('-total_quantity')[:limit]
        
        return list(top_products)
