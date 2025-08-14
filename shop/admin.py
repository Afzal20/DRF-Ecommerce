from django.contrib import admin
from django.utils.html import format_html
from django.http import JsonResponse
from django.urls import path
from django.core.cache import cache
from django.contrib import messages
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
    HeroSection, 
    TopSellingProducts,
    TopCategory,
    Category,  # Added Category import
)

admin.site.site_header = 'Welcome to Ecom Admin Panel'
admin.site.index_title = 'Ecom Admin Panel'

class DistrictsAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'sort_order', 'product_count']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['product_count']
    list_editable = ['sort_order']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'image')
        }),
        ('Status & Display', {
            'fields': ('sort_order',)
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        return obj.product_count
    product_count.short_description = 'Products Count'

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
    fields = ('image', 'image_order')
    readonly_fields = ('image_order',)

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
    list_display = ('product', 'image', 'image_order')
    list_editable = ('image_order',)
    search_fields = ('product__title',)
    list_filter = ('product__category',)

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

class TopSellingProductsAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'get_product_price', 'get_discounted_price', 'get_product_category', 
        'get_product_brand', 'get_product_stock', 'get_product_rating', 'get_availability_status'
    )
    search_fields = ('product__title', 'product__brand', 'product__category')
    list_filter = ('product__category', 'product__brand', 'product__availability_status')
    autocomplete_fields = ['product']
    readonly_fields = ('product_preview',)
    
    fieldsets = (
        (None, {
            'fields': ('product',)
        }),
        ('Product Details Preview', {
            'fields': ('product_preview',),
            'classes': ('collapse',),
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'product/<int:product_id>/preview/',
                self.admin_site.admin_view(self.product_preview_view),
                name='shop_product_preview'
            ),
        ]
        return custom_urls + urls
    
    def product_preview_view(self, request, product_id):
        """Return product data for preview in admin form"""
        try:
            product = Product.objects.get(id=product_id)
            data = {
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'category': product.category,
                'price': float(product.price),
                'discount_percentage': float(product.discount_percentage),
                'rating': float(product.rating),
                'stock': product.stock,
                'brand': product.brand,
                'sku': product.sku,
                'weight': float(product.weight),
                'availability_status': product.availability_status,
                'thumbnail': product.thumbnail.url if product.thumbnail else None,
            }
            return JsonResponse(data)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
    
    def product_preview(self, obj):
        """Display product preview in admin form"""
        if not obj or not obj.product:
            return format_html('<div style="padding: 20px; text-align: center; color: #6c757d; font-style: italic;">💡 Product preview will appear here after selecting a product</div>')
        
        product = obj.product
        
        # Calculate discounted price
        discounted_price = product.price
        savings = 0
        if product.discount_percentage > 0:
            savings = (product.price * product.discount_percentage) / 100
            discounted_price = product.price - savings
        
        # Stock status styling
        stock_style = 'background: #d4edda; color: #155724;'
        if product.stock <= 10:
            stock_style = 'background: #f8d7da; color: #721c24;'
        elif product.stock <= 50:
            stock_style = 'background: #fff3cd; color: #856404;'
        
        # Availability status
        availability_style = 'background: #f8d7da; color: #721c24;'
        availability_text = '❌ Not Available'
        if product.stock > 0 and product.availability_status.lower() == 'in stock':
            availability_style = 'background: #d4edda; color: #155724;'
            availability_text = '✅ Available'
        
        # Build price display
        price_html = ''
        if product.discount_percentage > 0:
            price_html = f'''
                <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <div style="text-decoration: line-through; color: #999; font-size: 14px;">Original: ${product.price}</div>
                    <div style="color: #e74c3c; font-weight: bold; font-size: 18px;">Sale Price: ${discounted_price:.2f}</div>
                    <div style="color: #27ae60; font-weight: bold;">You Save: ${savings:.2f} ({product.discount_percentage}% off)</div>
                </div>
            '''
        else:
            price_html = f'''
                <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <div style="color: #e74c3c; font-weight: bold; font-size: 18px;">Price: ${product.price}</div>
                </div>
            '''
        
        # Build thumbnail
        thumbnail_html = ''
        if product.thumbnail:
            thumbnail_html = f'<img src="{product.thumbnail.url}" alt="{product.title}" style="max-width: 150px; max-height: 150px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
        
        # Build description
        description_html = ''
        if product.description:
            description = product.description[:200] + ('...' if len(product.description) > 200 else '')
            description_html = f'''
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd;">
                    <strong>📝 Description:</strong>
                    <p style="margin-top: 8px; color: #555; line-height: 1.4;">{description}</p>
                </div>
            '''
        
        return format_html(f'''
            <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 15px; font-size: 18px; border-bottom: 2px solid #3498db; padding-bottom: 8px;">📋 Product Details</h3>
                
                <div style="display: flex; gap: 20px; align-items: flex-start;">
                    <div style="flex: 1;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">📦 Product:</span>
                                <span style="color: #333; font-weight: 500;">{product.title}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">🏷️ Category:</span>
                                <span style="color: #333; font-weight: 500;">{product.category}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">🏢 Brand:</span>
                                <span style="color: #333; font-weight: 500;">{product.brand}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">⭐ Rating:</span>
                                <span style="color: #333; font-weight: 500;">{product.rating}/5.0</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">📊 Stock:</span>
                                <span style="color: #333; font-weight: 500;"><span style="{stock_style} padding: 4px 8px; border-radius: 4px; font-weight: bold;">{product.stock} units</span></span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">🔄 Status:</span>
                                <span style="color: #333; font-weight: 500;"><span style="{availability_style} padding: 4px 8px; border-radius: 4px; font-weight: bold;">{availability_text}</span></span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">🏷️ SKU:</span>
                                <span style="color: #333; font-weight: 500;">{product.sku}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">⚖️ Weight:</span>
                                <span style="color: #333; font-weight: 500;">{product.weight} lbs</span>
                            </div>
                        </div>
                        {price_html}
                    </div>
                    {f'<div>{thumbnail_html}</div>' if thumbnail_html else ''}
                </div>
                {description_html}
            </div>
        ''')
    
    product_preview.short_description = "Product Preview"
    
    def get_product_price(self, obj):
        return f"${obj.product.price}"
    get_product_price.short_description = 'Original Price'
    get_product_price.admin_order_field = 'product__price'
    
    def get_discounted_price(self, obj):
        discounted = obj.discounted_price
        if discounted != obj.product.price:
            return format_html(
                '<span style="color: #e74c3c; font-weight: bold;">${}</span>',
                discounted
            )
        return f"${discounted}"
    get_discounted_price.short_description = 'Discounted Price'
    
    def get_product_category(self, obj):
        return obj.product.category
    get_product_category.short_description = 'Category'
    get_product_category.admin_order_field = 'product__category'
    
    def get_product_brand(self, obj):
        return obj.product.brand
    get_product_brand.short_description = 'Brand'
    get_product_brand.admin_order_field = 'product__brand'
    
    def get_product_stock(self, obj):
        stock = obj.product.stock
        if stock <= 10:
            return format_html(
                '<span style="color: #e74c3c; font-weight: bold;">{}</span>',
                stock
            )
        return stock
    get_product_stock.short_description = 'Stock'
    get_product_stock.admin_order_field = 'product__stock'
    
    def get_product_rating(self, obj):
        return f"{obj.product.rating} ⭐"
    get_product_rating.short_description = 'Rating'
    get_product_rating.admin_order_field = 'product__rating'
    
    def get_availability_status(self, obj):
        if obj.is_available:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">✓ Available</span>'
            )
        return format_html(
            '<span style="color: #e74c3c; font-weight: bold;">✗ Not Available</span>'
        )
    get_availability_status.short_description = 'Availability'


class TopCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'category', 'get_category_product_count', 'get_category_description', 'get_category_sort_order', 
        'get_is_active', 'get_category_meta_title'
    )
    search_fields = ('category__name', 'category__description', 'category__meta_title')
    list_filter = ('category__is_active', 'category__sort_order')
    autocomplete_fields = ['category']
    readonly_fields = ('category_preview',)
    
    fieldsets = (
        (None, {
            'fields': ('category',)
        }),
        ('Category Details Preview', {
            'fields': ('category_preview',),
            'classes': ('collapse',),
        }),
    )
    
    def get_category_product_count(self, obj):
        return obj.category_product_count
    get_category_product_count.short_description = 'Product Count'
    
    def get_category_description(self, obj):
        description = obj.category.description
        if description:
            return description[:50] + ('...' if len(description) > 50 else '')
        return '-'
    get_category_description.short_description = 'Description'
    
    def get_category_sort_order(self, obj):
        return obj.category.sort_order
    get_category_sort_order.short_description = 'Sort Order'
    get_category_sort_order.admin_order_field = 'category__sort_order'
    
    def get_is_active(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: #e74c3c; font-weight: bold;">✗ Inactive</span>'
        )
    get_is_active.short_description = 'Status'
    
    def get_category_meta_title(self, obj):
        meta_title = obj.category.meta_title
        if meta_title:
            return meta_title[:30] + ('...' if len(meta_title) > 30 else '')
        return '-'
    get_category_meta_title.short_description = 'Meta Title'
    
    def category_preview(self, obj):
        """Display category preview in admin form"""
        if not obj or not obj.category:
            return format_html('<div style="padding: 20px; text-align: center; color: #6c757d; font-style: italic;">💡 Category preview will appear here after selecting a category</div>')
        
        category = obj.category
        
        # Status styling
        status_style = 'background: #d4edda; color: #155724;' if category.is_active else 'background: #f8d7da; color: #721c24;'
        status_text = '✅ Active' if category.is_active else '❌ Inactive'
        
        # Build image display
        image_html = ''
        if category.image:
            image_html = f'<img src="{category.image.url}" alt="{category.name}" style="max-width: 150px; max-height: 150px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
        
        # Build description
        description_html = ''
        if category.description:
            description = category.description[:200] + ('...' if len(category.description) > 200 else '')
            description_html = f'''
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd;">
                    <strong>📝 Description:</strong>
                    <p style="margin-top: 8px; color: #555; line-height: 1.4;">{description}</p>
                </div>
            '''
        
        return format_html(f'''
            <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 15px; font-size: 18px; border-bottom: 2px solid #3498db; padding-bottom: 8px;">📂 Category Details</h3>
                
                <div style="display: flex; gap: 20px; align-items: flex-start;">
                    <div style="flex: 1;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">📂 Category:</span>
                                <span style="color: #333; font-weight: 500;">{category.name}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">🔗 Slug:</span>
                                <span style="color: #333; font-weight: 500;">{category.slug}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">📊 Products:</span>
                                <span style="color: #333; font-weight: 500;">{category.product_count}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">🔄 Status:</span>
                                <span style="color: #333; font-weight: 500;"><span style="{status_style} padding: 4px 8px; border-radius: 4px; font-weight: bold;">{status_text}</span></span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">🔢 Sort Order:</span>
                                <span style="color: #333; font-weight: 500;">{category.sort_order}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span style="font-weight: 600; color: #555;">🏷️ Meta Title:</span>
                                <span style="color: #333; font-weight: 500;">{category.meta_title or 'Not set'}</span>
                            </div>
                        </div>
                        
                        {description_html}
                    </div>
                    
                    <div style="flex-shrink: 0;">
                        {image_html}
                    </div>
                </div>
            </div>
        ''')
    category_preview.short_description = "Category Preview"


# Cache clearing admin actions
def clear_all_cache_action(modeladmin, request, queryset):
    """Admin action to clear all cache"""
    try:
        cache.clear()
        messages.success(request, "All cache has been cleared successfully!")
    except Exception as e:
        messages.error(request, f"Error clearing cache: {str(e)}")

clear_all_cache_action.short_description = "Clear all cache"


# Registering Models
admin.site.register(Districts, DistrictsAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Slider, SliderAdmin)
admin.site.register(BillingAddress, BillingAddressAdmin)
admin.site.register(Payment, PaymentAdmin)
# Register admin actions
admin.site.add_action(clear_all_cache_action)

admin.site.register(Coupon, CouponAdmin)
admin.site.register(Refund, RefundAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)

# New Product Models
admin.site.register(TopSellingProducts, TopSellingProductsAdmin)
admin.site.register(TopCategory, TopCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(HeroSection, HeroSectionAdmin)