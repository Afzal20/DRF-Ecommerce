from django.core.validators import RegexValidator
from rest_framework import serializers
from .models import (
    ContactMessage, Districts, HeroSection, OrderItem, Cart, Order,
    Slider, BillingAddress, Payment, Coupon, Refund, Product, ProductImage, ProductReview
)

class DistrictsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Districts
        fields = ['id', 'title']

class BillingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingAddress
        fields = ['id', 'user', 'street_address', 'apartment_address', 'country', 'zip']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user', 'amount', 'timestamp', 'payment_method', 'charge_id', 'success']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'amount']

class SliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slider
        fields = ['id', 'image', 'title']

class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['id', 'order', 'reason', 'accepted', 'email']

# Admin-related Serializers

class AdminBillingAddressSerializer(BillingAddressSerializer):
    class Meta(BillingAddressSerializer.Meta):
        fields = BillingAddressSerializer.Meta.fields

class AdminPaymentSerializer(PaymentSerializer):
    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields

class AdminCouponSerializer(CouponSerializer):
    class Meta(CouponSerializer.Meta):
        fields = CouponSerializer.Meta.fields

# from rest_framework import serializers
# from .models import Cart

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'

class AddToCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['title', 'price', 'quantity', 'total', 'discountPercentage', 'discountedTotal', 'thumbnail']

# Product Serializers
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url']

class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = ['id', 'rating', 'comment', 'date', 'reviewer_name', 'reviewer_email']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'category', 'price', 'discount_percentage', 
            'rating', 'stock', 'tags', 'brand', 'sku', 'weight', 'width', 'height', 
            'depth', 'warranty_information', 'shipping_information', 'availability_status',
            'return_policy', 'minimum_order_quantity', 'created_at', 'updated_at', 
            'barcode', 'qr_code', 'thumbnail', 'images', 'reviews'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'color', 'size', 'total_price']
        
class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'first_name', 'last_name', 'phone_number', 'district', 'upozila', 'city', 'address', 
            'payment_method', 'phone_number_payment', 'transaction_id', 'created_at', 'updated_at', 'order_items', 'total_price'
        ]
        read_only_fields = ['user', 'total_price']  # Prevent users from setting 'user' manually

    total_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        return obj.total_price

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user:
            validated_data["user"] = request.user
        
        order_items_data = validated_data.pop("order_items", [])
        order = Order.objects.create(**validated_data)

        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order


class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = ['id', 'title', 'offer', 'button_1_Text', 'button_2_Text', 'image'] 
