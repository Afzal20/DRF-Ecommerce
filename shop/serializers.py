from django.core.validators import RegexValidator
from rest_framework import serializers
from .models import (
    ContactMessage, Districts, Category, ItemType, OrderItem, Size, Rating, Color,
    Item, ItemImage, ItemSize, ItemColor, Cart, Order,
    Slider, BillingAddress, Payment, Coupon, Refund
)

class DistrictsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Districts
        fields = ['id', 'title']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ItemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemType
        fields = ['id', 'name']

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'name']

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'value']

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name', 'code']

class ItemImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemImage
        fields = ['id', 'image']

class ItemSizeSerializer(serializers.ModelSerializer):
    size = SizeSerializer()
    
    class Meta:
        model = ItemSize
        fields = ['id', 'size', 'price_for_this_size']

class ItemColorSerializer(serializers.ModelSerializer):
    color = ColorSerializer()
    
    class Meta:
        model = ItemColor
        fields = ['id', 'color']

class ItemSerializer(serializers.ModelSerializer):
    images = ItemImageSerializer(many=True)  # Get all related images
    item_size = ItemSizeSerializer(many=True)  # Get all related sizes with details
    item_color = ItemColorSerializer(many=True)  # Get all related colors with details
    category = CategorySerializer()  # Nested serializer for category
    type = ItemTypeSerializer()  # Nested serializer for item type
    ratings = RatingSerializer()  # Nested serializer for ratings

    class Meta:
        model = Item
        fields = [
            'id', 'title', 'image', 'ratings', 'price', 'number_of_items',
            'discount_price', 'product_id', 'brand_name', 'category', 'type',
            'description', 'is_featured', 'is_bestselling', 'images', 'item_size', 'item_color'
        ]

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
        read_only_fields = ['ordered', 'delivered', 'order_status']

class AddToCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['item', 'item_color_code', 'item_size', 'quantity', 'applied_coupon']

    def validate(self, attrs):
        user = self.context['request'].user
        item = attrs.get('item')
        quantity = attrs.get('quantity')

        # Check if the item has enough stock
        if item.number_of_items < quantity:
            raise serializers.ValidationError(f"Not enough stock for {item.title}.")

        # Check if the same item already exists in the cart
        if Cart.objects.filter(
            user_name=user, 
            item=item, 
            item_color_code=attrs.get('item_color_code'),
            item_size=attrs.get('item_size'), 
            ordered=False
        ).exists():
            raise serializers.ValidationError("This item is already in your cart.")
        
        return attrs

    def create(self, validated_data):
        validated_data['user_name'] = self.context['request'].user
        return super().create(validated_data)

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'title', 'image', 'price', 'number_of_items', 'discount_price', 'product_id', 'brand_name', 'category', 'type', 'description', 'is_featured', 'is_bestselling']



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
