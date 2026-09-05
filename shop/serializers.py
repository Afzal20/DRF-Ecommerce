from rest_framework import serializers

from .models import (
    BillingAddress,
    Cart,
    Category,
    Color,
    ContactMessage,
    Coupon,
    Districts,
    HeroSection,
    Item,
    ItemColor,
    ItemImage,
    ItemSize,
    ItemType,
    NewArrivalBanner,
    NewArrivalBannerImage,
    Order,
    OrderItem,
    Payment,
    Rating,
    Refund,
    SiteSetting,
    Size,
    Slider,
)


class ItemImageSerilizers(serializers.ModelSerializer):
    class Meta:
        model = ItemImage
        fields = "__all__"


class SizeSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = "__all__"


class ColorSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = "__all__"


class ItemSizeSerilizers(serializers.ModelSerializer):
    size = SizeSerilizers(read_only=True)

    class Meta:
        model = ItemSize
        fields = "__all__"


class ItemColorSerilizers(serializers.ModelSerializer):
    color = ColorSerilizers(read_only=True)

    class Meta:
        model = ItemColor
        fields = "__all__"


class ItemSerilizers(serializers.ModelSerializer):
    images = ItemImageSerilizers(many=True, read_only=True)
    item_size = ItemSizeSerilizers(many=True, read_only=True)
    item_color = ItemColorSerilizers(many=True, read_only=True)

    class Meta:
        model = Item
        fields = "__all__"


class CategorySerilizers(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ItemTypeSerilizers(serializers.ModelSerializer):
    class Meta:
        model = ItemType
        fields = "__all__"


class HeroSectionSerilizers(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = "__all__"


class DistrictsSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Districts
        fields = "__all__"


class ContactMessageSerilizers(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"


class SliderSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Slider
        fields = "__all__"


class BillingAddressSerilizers(serializers.ModelSerializer):
    class Meta:
        model = BillingAddress
        fields = "__all__"
        read_only_fields = ("user",)


class PaymentSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ("user", "success")


class CouponSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class RefundSerilizers(serializers.ModelSerializer):
    order = serializers.CharField(source="order.id", read_only=True)
    reason = serializers.CharField()
    accepted = serializers.BooleanField(read_only=True)
    email = serializers.EmailField()

    class Meta:
        model = Refund
        fields = "__all__"


class CartSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = "__all__"
        read_only_fields = ("user_name", "ordered", "delivered", "order_status")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["item"] = ItemSerilizers(
            instance.item, context=self.context
        ).data
        return representation


class OrderSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ("user", "ordered", "created_at", "updated_at")


class OrderItemSerilizers(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class RatingSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"


class NewArrivalBannerImageSerializer(serializers.ModelSerializer):
    final_image_url = serializers.ReadOnlyField()

    class Meta:
        model = NewArrivalBannerImage
        fields = (
            "id",
            "image_name",
            "image",
            "image_url",
            "final_image_url",
            "link_url",
            "order",
            "is_active",
        )


class NewArrivalBannerSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = NewArrivalBanner
        fields = (
            "id",
            "title",
            "subtitle",
            "discount_percent",
            "discount_text",
            "is_active",
            "images",
        )

    def get_images(self, obj):
        active_images = obj.images.filter(is_active=True).order_by("order", "id")
        return NewArrivalBannerImageSerializer(
            active_images, many=True, context=self.context
        ).data


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = (
            "id",
            "site_name",
            "hotline_label",
            "hotline_number",
            "announcement_badge",
            "announcement_text",
            "is_active",
        )
