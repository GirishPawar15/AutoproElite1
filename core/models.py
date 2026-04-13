# Models for AutoPro Elite

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Listing(models.Model):
    """Car listing model"""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    km = models.PositiveIntegerField(default=0)
    fuel = models.CharField(max_length=20, blank=True)
    trans = models.CharField(max_length=20, blank=True)
    price = models.PositiveIntegerField()
    original_predicted_price = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text='Original price from prediction before admin markup'
    )
    location = models.CharField(max_length=120, blank=True)
    img = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='approved_listings'
    )
    admin_notes = models.TextField(blank=True)
    description = models.TextField(blank=True)
    seller = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.make} {self.model} {self.year}"
    
    def get_markup_amount(self):
        """Calculate markup amount"""
        if self.original_predicted_price and self.price != self.original_predicted_price:
            return self.price - self.original_predicted_price
        return 0
    
    def get_markup_percentage(self):
        """Calculate markup percentage"""
        if self.original_predicted_price and self.original_predicted_price > 0:
            markup = self.price - self.original_predicted_price
            return (markup / self.original_predicted_price) * 100
        return 0
    
    def get_all_images(self):
        """Get all images for this listing"""
        images = list(self.images.all().values_list('image_url', flat=True))
        if self.img and self.img not in images:
            images.insert(0, self.img)
        return images if images else ['https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop']
    
    def get_primary_image(self):
        """Get primary image for this listing"""
        first_image = self.images.first()
        if first_image:
            return first_image.image_url
        return self.img or 'https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop'


class ListingImage(models.Model):
    """Multiple images for a car listing"""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField()
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.listing} (order: {self.order})"


class ContactMessage(models.Model):
    """Contact form submissions"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"


class UserActivity(models.Model):
    """Track user activities"""
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('add_to_cart', 'Add To Cart'),
        ('checkout', 'Checkout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"


class Cart(models.Model):
    """Shopping cart for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        return sum(item.price * item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Items in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_id = models.CharField(max_length=64)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image_url = models.URLField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product_id')

    def __str__(self):
        return f"{self.name} x{self.quantity}"


class Order(models.Model):
    """Customer orders"""
    ORDER_TYPE_CHOICES = [
        ('car', 'Car'),
        ('spare', 'Spare Part'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='orders'
    )
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    car_listing = models.ForeignKey(
        Listing,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='orders'
    )
    notes = models.CharField(max_length=255, blank=True)
    
    # E-Bill fields
    bill_number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    bill_date = models.DateTimeField(blank=True, null=True)
    bill_pdf_path = models.CharField(max_length=500, blank=True)
    bill_sent_email = models.BooleanField(default=False)
    
    # Customer details
    customer_name = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    delivery_address = models.TextField(blank=True)
    
    # Payment
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Pricing breakdown
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.username if self.user else 'Guest'}"


class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.CharField(max_length=64, blank=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image_url = models.URLField(blank=True)
    car_listing = models.ForeignKey(
        Listing,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='order_items'
    )

    def __str__(self):
        return f"{self.name} x{self.quantity} (Order #{self.order.id})"


class Profile(models.Model):
    """User profile with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar_url = models.URLField(blank=True)
    
    # Documents
    driving_license_number = models.CharField(max_length=40, blank=True)
    driving_license_image = models.URLField(blank=True)
    aadhar_number = models.CharField(max_length=20, blank=True)
    aadhar_image = models.URLField(blank=True)
    pan_number = models.CharField(max_length=20, blank=True)
    pan_image = models.URLField(blank=True)
    
    # Car information
    car_make = models.CharField(max_length=80, blank=True)
    car_model = models.CharField(max_length=80, blank=True)
    car_year = models.PositiveIntegerField(default=0)
    car_image = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


class SparePart(models.Model):
    """Spare parts catalog"""
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    compatible_make = models.CharField(max_length=100, blank=True)
    compatible_model = models.CharField(max_length=100, blank=True)
    compatible_year_from = models.PositiveIntegerField(blank=True, null=True)
    compatible_year_to = models.PositiveIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Spare Part'
        verbose_name_plural = 'Spare Parts'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"


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
    
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_transactions')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Transaction'
        verbose_name_plural = 'Stock Transactions'

    def __str__(self):
        return f"{self.transaction_type} - {self.spare_part.name} ({self.quantity})"
