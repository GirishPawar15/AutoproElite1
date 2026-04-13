from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from .models import (
    Listing,
    ListingImage,
    ContactMessage,
    UserActivity,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Profile,
    SparePart,
)

class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ('image_url', 'caption', 'order')
    ordering = ('order',)

@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sku",
        "name",
        "category",
        "price",
        "stock",
        "is_active",
        "updated_at",
    )
    list_filter = ("category", "is_active")
    search_fields = ("sku", "name", "compatible_make", "compatible_model")
    ordering = ("name",)

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("id", "make", "model", "year", "price", "original_price_display", "markup_display", "location", "status_badge", "seller", "created_at")
    search_fields = ("make", "model", "location", "seller__username")
    list_filter = ("status", "year", "fuel", "trans", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "approved_at", "approved_by", "original_predicted_price")
    inlines = [ListingImageInline]
    
    # Custom actions for approval workflow
    actions = ["approve_listings", "reject_listings"]
    
    # Fieldsets for better organization
    fieldsets = (
        ("Basic Information", {
            "fields": ("make", "model", "year", "km", "fuel", "trans", "location", "img")
        }),
        ("Pricing", {
            "fields": ("original_predicted_price", "price"),
            "description": "Original predicted price is stored when listing is created. Final price is automatically calculated with 10%% markup on approval."
        }),
        ("Approval Status", {
            "fields": ("status", "admin_notes", "approved_at", "approved_by")
        }),
        ("Seller Information", {
            "fields": ("seller",)
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
    
    def original_price_display(self, obj):
        if obj.original_predicted_price:
            return f"₹{obj.original_predicted_price:,}"
        return "-"
    original_price_display.short_description = "Original Price"
    original_price_display.admin_order_field = "original_predicted_price"
    
    def markup_display(self, obj):
        """Display markup amount and percentage with proper formatting"""
        if obj.original_predicted_price and obj.price != obj.original_predicted_price:
            markup_amount = obj.get_markup_amount()
            markup_percentage = obj.get_markup_percentage()
            # Pre-format the entire string to avoid any format_html issues
            formatted_text = f"+₹{markup_amount:,} ({markup_percentage:.1f}%)"
            return format_html(
                '<span style="color: #28A745; font-weight: bold;">{}</span>',
                formatted_text
            )
        return "-"
    markup_display.short_description = "Markup Applied"
    
    def status_badge(self, obj):
        colors = {
            "pending": "#FFA500",
            "approved": "#28A745", 
            "rejected": "#DC3545"
        }
        color = colors.get(obj.status, "#6C757D")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"
    
    def get_queryset(self, request):
        # By default, show pending listings first
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(status__in=["pending", "approved"])
    
    def approve_listings(self, request, queryset):
        count = 0
        total_markup = 0
        for listing in queryset:
            if listing.status != "approved":
                # Apply 10%% markup to original predicted price
                if listing.original_predicted_price:
                    original_price = listing.original_predicted_price
                    markup_price = int(listing.original_predicted_price * 1.10)
                    markup_amount = markup_price - original_price
                    total_markup += markup_amount
                    listing.price = markup_price
                
                listing.status = "approved"
                listing.approved_by = request.user
                listing.approved_at = timezone.now()
                listing.save()
                count += 1
        
        if count > 0:
            # Pre-format the markup amount to avoid formatting issues
            formatted_markup = f"{total_markup:,}"
            self.message_user(
                request, 
                f"Successfully approved {count} listing(s) with 10%% markup applied. Total markup added: ₹{formatted_markup}",
                messages.SUCCESS
            )
    approve_listings.short_description = "Approve selected listings (with 10%% markup)"
    
    def reject_listings(self, request, queryset):
        count = queryset.filter(status="pending").update(status="rejected")
        self.message_user(request, f"Successfully rejected {count} listing(s).")
    reject_listings.short_description = "Reject selected listings"
    
    def save_model(self, request, obj, form, change):
        # When approving through individual edit form
        if obj.status == "approved" and not obj.approved_by:
            # Apply 10%% markup to original predicted price if not already applied
            if obj.original_predicted_price and obj.price == obj.original_predicted_price:
                original_price = obj.original_predicted_price
                markup_price = int(obj.original_predicted_price * 1.10)
                markup_amount = markup_price - original_price
                obj.price = markup_price
                
                # Pre-format all amounts to avoid formatting issues
                formatted_original = f"{original_price:,}"
                formatted_final = f"{markup_price:,}"
                formatted_markup = f"{markup_amount:,}"
                
                messages.success(
                    request,
                    f"Listing approved with 10%% markup applied. Original: ₹{formatted_original} → Final: ₹{formatted_final} (Markup: +₹{formatted_markup})"
                )
            
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "subject", "created_at")
    search_fields = ("email", "subject")


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "action", "description", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("user__username", "description")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("product_id", "name", "price", "quantity", "image_url", "added_at")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_items", "total_price", "created_at", "updated_at")
    inlines = [CartItemInline]
    search_fields = ("user__username",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_id", "name", "price", "quantity", "image_url", "car_listing")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_type",
        "status",
        "user",
        "car_listing",
        "total_amount",
        "created_at",
    )
    list_filter = ("order_type", "status", "created_at")
    search_fields = ("id", "user__username", "notes")
    inlines = [OrderItemInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "phone", "car_make", "car_model", "car_year", "updated_at")
    search_fields = ("user__username", "full_name", "driving_license_number", "aadhar_number")
