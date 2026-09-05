from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    BillingAddress,
    Cart,
    Category,
    Color,
    ContactMessage,
    Coupon,
    Districts,
    Item,
    ItemColor,
    ItemImage,
    ItemSize,
    ItemType,
    Order,
    OrderItem,
    Payment,
    Rating,
    Refund,
    Size,
    Slider,
    Vendor,
)

admin.site.site_header = "Wellcome to Ecom Admin Panel"
admin.site.index_title = "Ecom Admin Panel"


# Inline Admin Models
class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1


class ItemSizeInline(admin.TabularInline):
    model = ItemSize
    extra = 1


class ItemColorInline(admin.TabularInline):
    model = ItemColor
    extra = 1


class ItemAdmin(admin.ModelAdmin):
    inlines = [ItemImageInline, ItemSizeInline, ItemColorInline]
    list_display = [
        "product_id",
        "title",
        "ratings",
        "price",
        "number_of_items",
        "discount_price",
        "brand_name",
        "category",
        "type",
        "get_first_image_url",
        "description",
        "vendor",
        "is_featured",
        "is_bestselling",
    ]

    def get_first_image_url(self, obj):
        first_image = obj.images.first()
        if first_image:
            return format_html(
                '<img src="{}" width="50" height="50" />', first_image.image.url
            )
        return None

    get_first_image_url.short_description = "First Image"


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]


class VendorAdmin(admin.ModelAdmin):
    list_display = ["store_name", "user", "created_at"]


class DistrictsAdmin(admin.ModelAdmin):
    list_display = ["title"]


class ItemTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]


class SizeAdmin(admin.ModelAdmin):
    list_display = ["name"]


class RatingAdmin(admin.ModelAdmin):
    list_display = ["value"]


class ColorAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]


class CartAdmin(admin.ModelAdmin):
    list_display = [
        "user_name",
        "item",
        "item_color_code",
        "item_size",
        "quantity",
        "ordered",
        "delivered",
        "applied_coupon",
    ]
    search_fields = ["user_name__email", "item__title"]
    list_filter = ["ordered", "delivered", "applied_coupon"]


class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ("user", "street_address", "apartment_address", "country", "zip")
    search_fields = ("user__email", "street_address", "apartment_address")
    list_filter = ("country",)


class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "amount",
        "timestamp",
        "payment_method",
        "charge_id",
        "success",
    )
    search_fields = ("user__email", "charge_id")
    list_filter = ("success", "payment_method")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)
    readonly_fields = ("timestamp",)

    @admin.display(description="Related Order")
    def related_order(self, obj):
        order = Order.objects.filter(transaction_id=obj.charge_id).first()
        if order:
            url = reverse("admin:shop_order_change", args=[order.id])
            return format_html('<a href="{}">Order #{}</a>', url, order.id)
        return "-"

    def get_list_display(self, request):
        return list(self.list_display) + ["related_order"]


class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "amount")
    search_fields = ("code",)


class RefundAdmin(admin.ModelAdmin):
    list_display = ("order", "reason", "accepted", "email")
    search_fields = ("order__id", "email")
    list_filter = ("accepted",)


class SliderAdmin(admin.ModelAdmin):
    list_display = ("title",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "first_name",
        "last_name",
        "created_at",
        "total_price",
        "ordered",
        "payment_method",
        "transaction_id",
    )
    search_fields = ("user__email", "first_name", "last_name", "transaction_id")
    list_filter = ("ordered", "payment_method")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "quantity", "price", "color", "size")


# Registering Models
admin.site.register(Districts, DistrictsAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ItemType, ItemTypeAdmin)
admin.site.register(Size, SizeAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(ItemImage)
admin.site.register(ItemSize)
admin.site.register(ItemColor)
admin.site.register(Cart, CartAdmin)
admin.site.register(Slider, SliderAdmin)
admin.site.register(BillingAddress, BillingAddressAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Refund, RefundAdmin)
admin.site.register(ContactMessage)
