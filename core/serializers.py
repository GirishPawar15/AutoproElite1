#authentication   signin profile tab


from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Listing, ListingImage, ContactMessage, UserActivity, CartItem, Cart, Profile, SparePart


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image_url', 'caption', 'order']
        read_only_fields = ['id']


class ListingSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField(read_only=True)
    seller_username = serializers.SerializerMethodField(read_only=True)
    seller_email = serializers.SerializerMethodField(read_only=True)
    seller_phone = serializers.SerializerMethodField(read_only=True)
    all_images = serializers.SerializerMethodField(read_only=True)
    primary_image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'make', 'model', 'year', 'km', 'fuel', 'trans', 'price',
            'location', 'img', 'all_images', 'primary_image', 'created_at', 'seller',
            'seller_username', 'seller_email', 'seller_phone', 'description',
        ]
        read_only_fields = ['id', 'created_at', 'seller', 'seller_username', 'seller_email', 'seller_phone', 'all_images', 'primary_image']

    def to_representation(self, instance):
        """Add images field conditionally if the table exists"""
        data = super().to_representation(instance)
        try:
            # Try to add images field
            images_data = ListingImageSerializer(instance.images.all(), many=True).data
            data['images'] = images_data
        except Exception:
            # ListingImage table doesn't exist yet, skip images field
            data['images'] = []
        return data

    def get_seller_username(self, obj):
        try:
            return obj.seller.username if obj.seller else ''
        except Exception:
            return ''

    def get_seller_email(self, obj):
        try:
            return obj.seller.email if obj.seller else ''
        except Exception:
            return ''

    def get_seller_phone(self, obj):
        try:
            prof = getattr(obj.seller, 'profile', None) if obj.seller else None
            return getattr(prof, 'phone', '') or ''
        except Exception:
            return ''
    
    def get_all_images(self, obj):
        try:
            return obj.get_all_images()
        except Exception:
            # Fallback if ListingImage table doesn't exist yet
            return [obj.img] if obj.img else []
    
    def get_primary_image(self, obj):
        try:
            return obj.get_primary_image()
        except Exception:
            # Fallback if ListingImage table doesn't exist yet
            return obj.img or 'https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop'


class SparePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = SparePart
        fields = [
            'id', 'sku', 'name', 'category', 'compatible_make', 'compatible_model',
            'compatible_year_from', 'compatible_year_to', 'price', 'stock',
            'image_url', 'description', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(write_only=True, required=True)
    phone = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'name', 'phone']
        read_only_fields = ['id']

    def create(self, validated_data):
        name = validated_data.pop('name')
        phone = validated_data.pop('phone')
        
        # Split name into first and last if possible, or just use as first_name
        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User(
            username=validated_data['username'], 
            email=validated_data.get('email', ''),
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(validated_data['password'])
        user.save()

        # Create/Update profile with phone
        Profile.objects.update_or_create(
            user=user,
            defaults={'phone': phone, 'full_name': name}
        )
        
        return user


class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = [
            'id', 'action', 'description', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['product_id', 'name', 'price', 'quantity', 'image_url', 'added_at']
        read_only_fields = ['added_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['user', 'items', 'total_items', 'total_price']
        read_only_fields = ['user', 'items', 'total_items', 'total_price']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'id', 'full_name', 'phone', 'avatar_url',
            'driving_license_number', 'driving_license_image',
            'aadhar_number', 'aadhar_image',
            'pan_number', 'pan_image',
            'car_make', 'car_model', 'car_year', 'car_image',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
