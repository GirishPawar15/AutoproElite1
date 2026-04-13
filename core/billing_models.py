# New models for Spare Parts Billing System
# Add these to backend/core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SalesReport(models.Model):
    """Daily sales summary report"""
    report_date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    total_items_sold = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-report_date']
        verbose_name = 'Sales Report'
        verbose_name_plural = 'Sales Reports'

    def __str__(self):
        return f"Sales Report - {self.report_date}"


class StockTransaction(models.Model):
    """Track all stock movements"""
    TRANSACTION_TYPES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
    ]
    
    spare_part = models.ForeignKey('SparePart', on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_transactions')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Transaction'
        verbose_name_plural = 'Stock Transactions'

    def __str__(self):
        return f"{self.transaction_type} - {self.spare_part.name} ({self.quantity})"
