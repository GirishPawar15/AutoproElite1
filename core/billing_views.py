"""
API Views for Spare Parts Billing System
Add these to backend/core/views.py or import in urls.py
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from datetime import datetime, timedelta
from .models import SparePart, Order, OrderItem, SalesReport, StockTransaction
from .billing_service import BillingService
from .serializers import SparePartSerializer


def is_admin(user):
    """Check if user is admin or staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_admin, login_url='/login/')
def admin_analytics_view(request):
    """Render admin analytics dashboard - Admin only"""
    return render(request, 'admin-analytics.html')


@api_view(['POST'])
@permission_classes([AllowAny])
def create_pos_bill(request):
    """
    Create a bill from POS interface
    
    POST /api/billing/pos/create/
    {
        "items": [
            {"sku": "SP001", "quantity": 2},
            {"sku": "SP002", "quantity": 1}
        ],
        "customer": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+91-9876543210"
        },
        "payment_method": "cash",
        "apply_gst": true
    }
    """
    try:
        items = request.data.get('items', [])
        customer_data = request.data.get('customer', {})
        payment_method = request.data.get('payment_method', 'cash')
        apply_gst = request.data.get('apply_gst', True)
        
        if not items:
            return Response(
                {'error': 'No items provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user if authenticated
        if request.user.is_authenticated:
            customer_data['user'] = request.user
        
        # Create bill
        order = BillingService.create_spare_parts_bill(
            items=items,
            customer_data=customer_data,
            payment_method=payment_method,
            apply_gst=apply_gst
        )
        
        if not order:
            return Response(
                {'error': 'Failed to create bill'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'success': True,
            'order_id': order.id,
            'bill_number': order.bill_number,
            'total_amount': float(order.total_amount),
            'subtotal': float(order.subtotal),
            'tax_amount': float(order.tax_amount),
            'pdf_path': order.bill_pdf_path,
            'message': 'Bill created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Error creating bill: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def search_spare_parts(request):
    """
    Search spare parts for POS
    
    GET /api/billing/spare-parts/search/?q=brake
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        # Return all active spare parts
        spare_parts = SparePart.objects.filter(is_active=True)[:50]
    else:
        # Search by name, SKU, or category
        spare_parts = SparePart.objects.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__icontains=query),
            is_active=True
        )[:50]
    
    serializer = SparePartSerializer(spare_parts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_low_stock_items(request):
    """
    Get spare parts with low stock - Admin only
    
    GET /api/billing/low-stock/?threshold=10
    """
    threshold = int(request.GET.get('threshold', 10))
    low_stock_items = BillingService.get_low_stock_items(threshold)
    serializer = SparePartSerializer(low_stock_items, many=True)
    
    return Response({
        'count': low_stock_items.count(),
        'threshold': threshold,
        'items': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_sales_report(request):
    """
    Get sales report for date range - Admin only
    
    GET /api/billing/reports/sales/?start_date=2026-02-01&end_date=2026-02-07
    """
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        # Default to last 7 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    summary = BillingService.get_sales_summary(start_date, end_date)
    
    return Response({
        'start_date': start_date,
        'end_date': end_date,
        'summary': summary
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_top_selling_products(request):
    """
    Get top selling spare parts - Admin only
    
    GET /api/billing/reports/top-products/?limit=10&days=30
    """
    limit = int(request.GET.get('limit', 10))
    days = int(request.GET.get('days', 30))
    
    top_products = BillingService.get_top_selling_products(limit, days)
    
    return Response({
        'period_days': days,
        'products': top_products
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_daily_sales(request):
    """
    Get daily sales summary - Admin only
    
    GET /api/billing/reports/daily/?date=2026-02-06
    """
    date_str = request.GET.get('date')
    
    if date_str:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        report_date = datetime.now().date()
    
    orders = Order.objects.filter(
        order_type='spare',
        created_at__date=report_date
    )
    
    total_sales = sum(order.total_amount for order in orders)
    total_orders = orders.count()
    total_items = sum(order.items.count() for order in orders)
    
    return Response({
        'date': report_date,
        'total_sales': float(total_sales),
        'total_orders': total_orders,
        'total_items_sold': total_items,
        'average_order_value': float(total_sales / total_orders) if total_orders > 0 else 0
    })


@user_passes_test(is_admin, login_url='/login/')
def profit_analysis_view(request):
    """Render profit analysis dashboard - Admin only"""
    return render(request, 'profit-analysis.html')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_profit_analysis(request):
    """
    Get profit analysis data - Admin only
    Works with ALL existing order data including user purchases
    
    GET /api/billing/profit-analysis/?period=daily&start_date=2026-01-01&end_date=2026-02-07
    """
    period = request.GET.get('period', 'daily')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        end_date = datetime.now().date()
        if period == 'daily':
            start_date = end_date - timedelta(days=30)
        elif period == 'weekly':
            start_date = end_date - timedelta(days=84)
        elif period == 'monthly':
            start_date = end_date - timedelta(days=365)
        else:  # yearly
            start_date = end_date - timedelta(days=1825)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Get ALL orders in date range (including pending, paid, completed)
    # Only exclude cancelled orders
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).exclude(status='cancelled')
    
    print(f"Found {orders.count()} orders between {start_date} and {end_date}")
    
    # Calculate profit (assuming 30% profit margin for simplicity)
    # In real scenario, you'd have cost data in your models
    total_revenue = sum(float(order.total_amount) for order in orders)
    total_cost = total_revenue * 0.7  # 70% cost, 30% profit
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    print(f"Total Revenue: {total_revenue}, Total Profit: {total_profit}")
    
    # Generate chart data based on period
    chart_data = generate_chart_data(orders, period, start_date, end_date)
    
    # Distribution by order type
    spare_orders = [o for o in orders if o.order_type == 'spare']
    car_orders = [o for o in orders if o.order_type == 'car']
    
    spare_revenue = sum(float(o.total_amount) for o in spare_orders)
    car_revenue = sum(float(o.total_amount) for o in car_orders)
    
    distribution = {
        'spare_parts': spare_revenue * 0.3,  # 30% profit
        'cars': car_revenue * 0.3,
        'services': 0
    }
    
    # Comparison data
    comparison = generate_comparison_data(period, start_date, end_date)
    
    # Table data
    table_data = generate_table_data(orders, period, start_date, end_date)
    
    # Insights
    insights = generate_insights(total_profit, total_revenue, profit_margin, orders.count())
    
    # Calculate changes (compare with previous period)
    period_length = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_length)
    prev_end = start_date - timedelta(days=1)
    
    prev_orders = Order.objects.filter(
        created_at__date__gte=prev_start,
        created_at__date__lte=prev_end
    ).exclude(status='cancelled')
    
    prev_revenue = sum(float(o.total_amount) for o in prev_orders)
    prev_profit = prev_revenue * 0.3
    
    profit_change = ((total_profit - prev_profit) / prev_profit * 100) if prev_profit > 0 else 0
    revenue_change = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    
    return Response({
        'summary': {
            'total_profit': total_profit,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'profit_margin': profit_margin,
            'profit_change': profit_change,
            'revenue_change': revenue_change,
            'cost_change': revenue_change,  # Cost follows revenue
            'margin_change': 0  # Margin is fixed at 30% in this example
        },
        'chart_data': chart_data,
        'distribution': distribution,
        'comparison': comparison,
        'table_data': table_data,
        'insights': insights
    })


def generate_chart_data(orders, period, start_date, end_date):
    """Generate chart data based on period - includes ALL orders"""
    labels = []
    profit_data = []
    revenue_data = []
    cost_data = []
    
    # Convert queryset to list for easier filtering
    orders_list = list(orders)
    print(f"Generating chart data for {len(orders_list)} orders")
    
    if period == 'daily':
        current = start_date
        while current <= end_date:
            day_orders = [o for o in orders_list if o.created_at.date() == current]
            revenue = sum(float(o.total_amount) for o in day_orders)
            cost = revenue * 0.7
            profit = revenue * 0.3
            
            labels.append(current.strftime('%b %d'))
            revenue_data.append(revenue)
            cost_data.append(cost)
            profit_data.append(profit)
            
            if revenue > 0:
                print(f"  {current}: {len(day_orders)} orders, Revenue: ₹{revenue:.2f}, Profit: ₹{profit:.2f}")
            
            current += timedelta(days=1)
    
    elif period == 'weekly':
        current = start_date
        week_num = 1
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            week_orders = [o for o in orders_list if current <= o.created_at.date() <= week_end]
            revenue = sum(float(o.total_amount) for o in week_orders)
            cost = revenue * 0.7
            profit = revenue * 0.3
            
            labels.append(f'Week {week_num}')
            revenue_data.append(revenue)
            cost_data.append(cost)
            profit_data.append(profit)
            
            if revenue > 0:
                print(f"  Week {week_num}: {len(week_orders)} orders, Revenue: ₹{revenue:.2f}, Profit: ₹{profit:.2f}")
            
            current = week_end + timedelta(days=1)
            week_num += 1
    
    elif period == 'monthly':
        # Get unique months in the date range
        current = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        
        while current <= end_month:
            # Get all orders in this month
            month_orders = [o for o in orders_list 
                          if o.created_at.date().year == current.year 
                          and o.created_at.date().month == current.month]
            revenue = sum(float(o.total_amount) for o in month_orders)
            cost = revenue * 0.7
            profit = revenue * 0.3
            
            labels.append(current.strftime('%b %Y'))
            revenue_data.append(revenue)
            cost_data.append(cost)
            profit_data.append(profit)
            
            if revenue > 0:
                print(f"  {current.strftime('%b %Y')}: {len(month_orders)} orders, Revenue: ₹{revenue:.2f}, Profit: ₹{profit:.2f}")
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
    
    else:  # yearly
        current_year = start_date.year
        end_year = end_date.year
        while current_year <= end_year:
            year_orders = [o for o in orders_list if o.created_at.date().year == current_year]
            revenue = sum(float(o.total_amount) for o in year_orders)
            cost = revenue * 0.7
            profit = revenue * 0.3
            
            labels.append(str(current_year))
            revenue_data.append(revenue)
            cost_data.append(cost)
            profit_data.append(profit)
            
            if revenue > 0:
                print(f"  {current_year}: {len(year_orders)} orders, Revenue: ₹{revenue:.2f}, Profit: ₹{profit:.2f}")
            
            current_year += 1
    
    print(f"Chart data generated: {len(labels)} data points")
    return {
        'labels': labels,
        'profit': profit_data,
        'revenue': revenue_data,
        'cost': cost_data
    }


def generate_comparison_data(period, start_date, end_date):
    """Generate comparison data for bar chart"""
    labels = []
    values = []
    
    # Compare current period with previous periods
    periods = ['Current', 'Previous', '2 Periods Ago']
    period_length = (end_date - start_date).days
    
    for i, label in enumerate(periods):
        period_start = start_date - timedelta(days=period_length * i)
        period_end = end_date - timedelta(days=period_length * i)
        
        orders = Order.objects.filter(
            created_at__date__gte=period_start,
            created_at__date__lte=period_end
        ).exclude(status='cancelled')
        
        revenue = sum(float(o.total_amount) for o in orders)
        profit = revenue * 0.3
        
        labels.append(label)
        values.append(profit)
    
    return {
        'labels': labels,
        'values': values
    }


def generate_table_data(orders, period, start_date, end_date):
    """Generate table data - includes ALL orders"""
    table_data = []
    orders_list = list(orders)
    
    if period == 'daily':
        current = start_date
        while current <= end_date:
            day_orders = [o for o in orders_list if o.created_at.date() == current]
            revenue = sum(float(o.total_amount) for o in day_orders)
            cost = revenue * 0.7
            profit = revenue * 0.3
            margin = 30.0
            order_count = len(day_orders)
            avg_profit = profit / order_count if order_count > 0 else 0
            
            # Only add rows with data
            if order_count > 0:
                table_data.append({
                    'period': current.strftime('%Y-%m-%d'),
                    'revenue': revenue,
                    'cost': cost,
                    'profit': profit,
                    'margin': margin,
                    'orders': order_count,
                    'avg_profit': avg_profit
                })
            
            current += timedelta(days=1)
    
    elif period == 'weekly':
        current = start_date
        week_num = 1
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            week_orders = [o for o in orders_list if current <= o.created_at.date() <= week_end]
            revenue = sum(float(o.total_amount) for o in week_orders)
            cost = revenue * 0.7
            profit = revenue * 0.3
            margin = 30.0
            order_count = len(week_orders)
            avg_profit = profit / order_count if order_count > 0 else 0
            
            if order_count > 0:
                table_data.append({
                    'period': f'Week {week_num} ({current.strftime("%b %d")} - {week_end.strftime("%b %d")})',
                    'revenue': revenue,
                    'cost': cost,
                    'profit': profit,
                    'margin': margin,
                    'orders': order_count,
                    'avg_profit': avg_profit
                })
            
            current = week_end + timedelta(days=1)
            week_num += 1
    
    elif period == 'monthly':
        current = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        
        while current <= end_month:
            month_orders = [o for o in orders_list 
                          if o.created_at.date().year == current.year 
                          and o.created_at.date().month == current.month]
            revenue = sum(float(o.total_amount) for o in month_orders)
            cost = revenue * 0.7
            profit = revenue * 0.3
            margin = 30.0
            order_count = len(month_orders)
            avg_profit = profit / order_count if order_count > 0 else 0
            
            if order_count > 0:
                table_data.append({
                    'period': current.strftime('%B %Y'),
                    'revenue': revenue,
                    'cost': cost,
                    'profit': profit,
                    'margin': margin,
                    'orders': order_count,
                    'avg_profit': avg_profit
                })
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
    
    else:  # yearly
        current_year = start_date.year
        end_year = end_date.year
        while current_year <= end_year:
            year_orders = [o for o in orders_list if o.created_at.date().year == current_year]
            revenue = sum(float(o.total_amount) for o in year_orders)
            cost = revenue * 0.7
            profit = revenue * 0.3
            margin = 30.0
            order_count = len(year_orders)
            avg_profit = profit / order_count if order_count > 0 else 0
            
            if order_count > 0:
                table_data.append({
                    'period': str(current_year),
                    'revenue': revenue,
                    'cost': cost,
                    'profit': profit,
                    'margin': margin,
                    'orders': order_count,
                    'avg_profit': avg_profit
                })
            
            current_year += 1
    
    # Reverse to show most recent first
    table_data.reverse()
    
    print(f"Table data generated: {len(table_data)} rows")
    return table_data


def generate_insights(profit, revenue, margin, order_count):
    """Generate insights based on data"""
    insights = []
    
    if profit > 0:
        insights.append({
            'type': 'info',
            'icon': 'fa-check-circle',
            'message': f'Great! You made ₹{profit:,.0f} profit in this period.'
        })
    
    if margin > 25:
        insights.append({
            'type': 'info',
            'icon': 'fa-chart-line',
            'message': f'Healthy profit margin of {margin:.1f}% maintained.'
        })
    else:
        insights.append({
            'type': 'warning',
            'icon': 'fa-exclamation-triangle',
            'message': f'Profit margin is {margin:.1f}%. Consider optimizing costs.'
        })
    
    if order_count > 0:
        avg_profit_per_order = profit / order_count
        insights.append({
            'type': 'info',
            'icon': 'fa-money-bill-wave',
            'message': f'Average profit per order: ₹{avg_profit_per_order:,.0f}'
        })
    
    return insights
