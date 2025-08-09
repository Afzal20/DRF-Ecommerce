from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ContactMessage, 
    Districts, 
    Order, 
    OrderItem,
    Cart, 
    Slider, 
    BillingAddress, 
    Payment, 
    Coupon, 
    Refund,
    Product, 
    ProductImage, 
    ProductReview, 
    HeroSection
)

admin.site.site_header = 'Welcome to Ecom Admin Panel'
admin.site.index_title = 'Ecom Admin Panel'

class DistrictsAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']

class CartAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'quantity', 'total', 'discountPercentage', 'discountedTotal']
    search_fields = ['title']
    list_filter = ['discountPercentage']

class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'street_address', 'apartment_address', 'country', 'zip')
    search_fields = ('user__username', 'street_address', 'apartment_address')
    list_filter = ('country',)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'timestamp', 'payment_method', 'charge_id', 'success')
    search_fields = ('user__username', 'charge_id')
    list_filter = ('success', 'payment_method')

class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'amount')
    search_fields = ('code',)

class RefundAdmin(admin.ModelAdmin):
    list_display = ('order', 'reason', 'accepted', 'email')
    search_fields = ('order__id', 'email')
    list_filter = ('accepted',)

class SliderAdmin(admin.ModelAdmin):
    list_display = ('title',)

# New Product Models Admin Classes
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image_url',)

class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    fields = ('rating', 'comment', 'reviewer_name', 'reviewer_email', 'date')
    readonly_fields = ('date',)

class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'brand', 'category', 'price', 'discount_percentage', 
        'rating', 'stock', 'availability_status', 'created_at'
    )
    list_filter = ('category', 'brand', 'availability_status', 'created_at')
    search_fields = ('title', 'brand', 'sku', 'category')
    inlines = [ProductImageInline, ProductReviewInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'brand', 'sku')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_percentage')
        }),
        ('Inventory', {
            'fields': ('stock', 'availability_status', 'minimum_order_quantity')
        }),
        ('Product Details', {
            'fields': ('rating', 'weight', 'width', 'height', 'depth', 'barcode', 'qr_code', 'thumbnail')
        }),
        ('Policies & Information', {
            'fields': ('warranty_information', 'shipping_information', 'return_policy')
        }),
        ('Metadata', {
            'fields': ('tags', 'created_at', 'updated_at')
        }),
    )

class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_url')
    search_fields = ('product__title',)

class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'reviewer_name', 'rating', 'date')
    list_filter = ('rating', 'date')
    search_fields = ('product__title', 'reviewer_name', 'reviewer_email')
    readonly_fields = ('date',)

class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'offer', 'button_1_Text', 'button_2_Text')
    search_fields = ('title', 'offer')

# Order and OrderItem Admin Classes
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('product', 'quantity', 'price', 'color', 'size')
    readonly_fields = ('total_price',)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'created_at', 'total_price', 'ordered')
    list_filter = ('ordered', 'created_at', 'payment_method')
    search_fields = ('first_name', 'last_name', 'phone_number')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at', 'total_price')

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'color', 'size', 'total_price')
    list_filter = ('color', 'size')
    search_fields = ('order__first_name', 'order__last_name', 'product')

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('email', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('email', 'subject')
    readonly_fields = ('created_at',)

# Registering Models
admin.site.register(Districts, DistrictsAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Slider, SliderAdmin)
admin.site.register(BillingAddress, BillingAddressAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Refund, RefundAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)

# New Product Models
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(HeroSection, HeroSectionAdmin)