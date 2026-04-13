"""
URL Configuration for Billing Module
Add these to backend/core/urls.py
"""

from django.urls import path
from .billing_views import (
    admin_analytics_view,
    create_pos_bill,
    search_spare_parts,
    get_low_stock_items,
    get_sales_report,
    get_top_selling_products,
    get_daily_sales,
)

# Add these to your existing urlpatterns
billing_urlpatterns = [
    # Admin Analytics Dashboard
    path('admin/analytics/', admin_analytics_view, name='admin_analytics'),
    
    # POS Billing
    path('billing/pos/create/', create_pos_bill, name='create_pos_bill'),
    path('billing/spare-parts/search/', search_spare_parts, name='search_spare_parts'),
    
    # Reports
    path('billing/reports/sales/', get_sales_report, name='sales_report'),
    path('billing/reports/daily/', get_daily_sales, name='daily_sales'),
    path('billing/reports/top-products/', get_top_selling_products, name='top_products'),
    path('billing/low-stock/', get_low_stock_items, name='low_stock_items'),
]
