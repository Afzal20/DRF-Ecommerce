from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

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
        "get_thumbnail",
        "get_title_with_sku",
        "category",
        "price",
        "discount_price",
        "stock_badge",
        "ratings_stars",
        "is_featured",
        "is_bestselling",
    ]
    list_display_links = ["get_thumbnail", "get_title_with_sku"]
    list_editable = ["price", "discount_price", "is_featured", "is_bestselling"]
    search_fields = [
        "title",
        "product_id",
        "brand_name",
        "category__name",
        "description",
    ]
    list_filter = ["category", "type", "is_featured", "is_bestselling", "vendor"]
    list_per_page = 20
    ordering = ["-id"]

    @admin.display(description="Image")
    def get_thumbnail(self, obj):
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html(
                '<img src="{}" style="width:44px; height:44px; object-fit:contain; border-radius:6px; border:1px solid #cbd5e1; background:#ffffff; padding:2px;" />',
                first_image.image.url,
            )
        return mark_safe(
            '<div style="width:44px; height:44px; border-radius:6px; border:1px dashed #cbd5e1; display:flex; align-items:center; justify-content:center; color:#94a3b8; font-size:9px; font-weight:700; background:#f8fafc;">NO IMG</div>'
        )

    @admin.display(description="Product Details", ordering="title")
    def get_title_with_sku(self, obj):
        brand_html = (
            f'<span style="color:#64748b; font-size:11px; margin-right:4px;">{obj.brand_name}</span>'
            if obj.brand_name
            else ""
        )
        sku_html = (
            f'<span style="background:#f1f5f9; color:#475569; font-size:10px; font-weight:700; padding:1px 5px; border-radius:4px; border:1px solid #e2e8f0; font-family:monospace;">{obj.product_id}</span>'
            if obj.product_id
            else ""
        )
        return format_html(
            '<div style="display:flex; flex-direction:column; gap:2px;">'
            '<span style="font-weight:700; color:#0f172a; font-size:13px; line-height:1.2;">{}</span>'
            '<div style="display:flex; align-items:center; gap:4px;">{}{}</div>'
            "</div>",
            obj.title,
            mark_safe(brand_html),
            mark_safe(sku_html),
        )

    @admin.display(description="Stock", ordering="number_of_items")
    def stock_badge(self, obj):
        qty = obj.number_of_items or 0
        if qty > 10:
            return format_html(
                '<span style="background:#dcfce7; color:#15803d; font-size:11px; font-weight:700; padding:2px 8px; border-radius:9999px; display:inline-block;">In Stock ({})</span>',
                qty,
            )
        elif qty > 0:
            return format_html(
                '<span style="background:#fef3c7; color:#b45309; font-size:11px; font-weight:700; padding:2px 8px; border-radius:9999px; display:inline-block;">Low ({})</span>',
                qty,
            )
        return mark_safe(
            '<span style="background:#fee2e2; color:#b91c1c; font-size:11px; font-weight:700; padding:2px 8px; border-radius:9999px; display:inline-block;">Out of Stock</span>'
        )

    @admin.display(description="Rating", ordering="ratings")
    def ratings_stars(self, obj):
        if (
            obj.ratings
            and hasattr(obj.ratings, "value")
            and obj.ratings.value is not None
        ):
            try:
                num = int(obj.ratings.value)
            except (ValueError, TypeError):
                num = 5
            num = max(0, min(5, num))
            return format_html(
                '<span style="color:#eab308; font-size:12px; letter-spacing:1px;" title="{} Stars">{}</span>',
                num,
                "★" * num + "☆" * (5 - num),
            )
        return mark_safe('<span style="color:#94a3b8; font-size:11px;">N/A</span>')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "get_item_count"]
    search_fields = ["name"]

    @admin.display(description="Total Products")
    def get_item_count(self, obj):
        return obj.item_set.count()


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
        "get_order_badge",
        "get_customer_info",
        "total_price_formatted",
        "ordered_status",
        "payment_method_badge",
        "created_at_formatted",
        "transaction_code",
    )
    list_display_links = ("get_order_badge", "get_customer_info")
    search_fields = ("user__email", "first_name", "last_name", "transaction_id")
    list_filter = ("ordered", "payment_method", "created_at")
    list_per_page = 20
    ordering = ("-created_at",)
    inlines = [OrderItemInline]

    @admin.display(description="Order #", ordering="id")
    def get_order_badge(self, obj):
        return format_html(
            '<span style="background:#eff6ff; color:#1d4ed8; font-weight:800; font-size:12px; padding:3px 8px; border-radius:6px; border:1px solid #bfdbfe; font-family:monospace;">#{}</span>',
            obj.id,
        )

    @admin.display(description="Customer")
    def get_customer_info(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip() or "Guest Customer"
        email = obj.user.email if obj.user else "N/A"
        return format_html(
            '<div style="line-height:1.2;">'
            '<span style="font-weight:700; color:#0f172a; font-size:13px;">{}</span><br>'
            '<span style="color:#64748b; font-size:11px;">{}</span>'
            "</div>",
            name,
            email,
        )

    @admin.display(description="Total")
    def total_price_formatted(self, obj):
        try:
            val = f"${float(obj.total_price):.2f}"
        except (ValueError, TypeError):
            val = "$0.00"
        return format_html(
            '<span style="font-weight:800; color:#0f172a; font-size:13px;">{}</span>',
            val,
        )

    @admin.display(description="Status", ordering="ordered")
    def ordered_status(self, obj):
        if obj.ordered:
            return mark_safe(
                '<span style="background:#dcfce7; color:#15803d; font-size:11px; font-weight:700; padding:3px 8px; border-radius:9999px;">Paid & Placed</span>'
            )
        return mark_safe(
            '<span style="background:#f1f5f9; color:#64748b; font-size:11px; font-weight:700; padding:3px 8px; border-radius:9999px;">Pending</span>'
        )

    @admin.display(description="Payment Method", ordering="payment_method")
    def payment_method_badge(self, obj):
        method = obj.payment_method or "Unknown"
        return format_html(
            '<span style="background:#f8fafc; color:#334155; font-size:11px; font-weight:600; padding:3px 8px; border-radius:6px; border:1px solid #cbd5e1;">{}</span>',
            method,
        )

    @admin.display(description="Created Date", ordering="created_at")
    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%b %d, %Y %H:%M") if obj.created_at else "-"

    @admin.display(description="Transaction ID")
    def transaction_code(self, obj):
        if obj.transaction_id:
            return format_html(
                '<code style="font-size:10px; background:#f1f5f9; color:#475569; padding:2px 5px; border-radius:4px;">{}</code>',
                (
                    obj.transaction_id[:16] + "..."
                    if len(obj.transaction_id) > 16
                    else obj.transaction_id
                ),
            )
        return mark_safe('<span style="color:#94a3b8; font-size:11px;">-</span>')


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


class NewArrivalBannerImageInline(admin.TabularInline):
    model = NewArrivalBannerImage
    extra = 1
    fields = ("image_name", "image", "image_url", "link_url", "order", "is_active")


@admin.register(NewArrivalBanner)
class NewArrivalBannerAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "discount_percent",
        "discount_text",
        "is_active",
        "updated_at",
    )
    list_editable = ("is_active",)
    inlines = [NewArrivalBannerImageInline]


@admin.register(NewArrivalBannerImage)
class NewArrivalBannerImageAdmin(admin.ModelAdmin):
    list_display = (
        "get_preview",
        "image_name",
        "banner",
        "order",
        "is_active",
        "created_at",
    )
    list_display_links = ("get_preview", "image_name")
    list_filter = ("is_active", "banner")
    list_editable = ("order", "is_active")
    search_fields = ("image_name",)

    @admin.display(description="Preview")
    def get_preview(self, obj):
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="width:60px; height:36px; object-fit:cover; border-radius:4px; border:1px solid #cbd5e1;" />',
                url,
            )
        return "-"


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = (
        "site_name",
        "hotline_label",
        "hotline_number",
        "announcement_badge",
        "announcement_text",
        "is_active",
        "updated_at",
    )
    list_editable = ("hotline_label", "hotline_number", "is_active")
    search_fields = ("site_name", "hotline_number")
