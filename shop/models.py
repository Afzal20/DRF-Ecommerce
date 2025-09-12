from django.conf import settings
from django.db import models
from uuid import uuid4
from django.utils import timezone
from django.shortcuts import reverse
from django.contrib.auth.models import User
from django_countries.fields import CountryField
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.apps import apps
from decimal import Decimal
from django.conf import settings

from django.utils.translation import gettext_lazy as _
    
from django.contrib.auth import get_user_model

User = settings.AUTH_USER_MODEL

class Districts(models.Model):
    title = models.CharField(_("Title"), max_length=100, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("District")
        verbose_name_plural = _("Districts")


class Category(models.Model):
    name = models.CharField(_("Name"), max_length=100, unique=True)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    image = models.ImageField(_("Image"), upload_to='categories/', blank=True, null=True)
    sort_order = models.PositiveIntegerField(_("Sort Order"), default=0)
    meta_title = models.CharField(_("Meta Title"), max_length=200, blank=True)  # SEO
    meta_description = models.CharField(_("Meta Description"), max_length=300, blank=True)  # SEO

    is_active = models.BooleanField(_("Is Active"), default=True)
    
    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        Product = apps.get_model('shop', 'Product')
        return Product.objects.filter(category=self).count()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

## THIS CHANGE FOR 'dummy' PRODUCTS
class Product(models.Model):
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"))
    category = models.ForeignKey(Category, verbose_name=_("Category"), on_delete=models.CASCADE)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(_("Discount Percentage"), max_digits=5, decimal_places=2)
    rating = models.DecimalField(_("Rating"), max_digits=3, decimal_places=2)
    stock = models.PositiveIntegerField(_("Stock"))
    tags = models.JSONField(_("Tags"), default=list, blank=True)  # List of strings
    brand = models.CharField(_("Brand"), max_length=100)
    sku = models.CharField(_("SKU"), max_length=100, unique=True)
    weight = models.DecimalField(_("Weight"), max_digits=10, decimal_places=2)

    # Dimensions
    width = models.DecimalField(_("Width"), max_digits=10, decimal_places=2)
    height = models.DecimalField(_("Height"), max_digits=10, decimal_places=2)
    depth = models.DecimalField(_("Depth"), max_digits=10, decimal_places=2)

    warranty_information = models.CharField(_("Warranty Information"), max_length=255, blank=True)
    shipping_information = models.CharField(_("Shipping Information"), max_length=255, blank=True)
    availability_status = models.CharField(_("Availability Status"), max_length=50)

    # Policies
    return_policy = models.CharField(_("Return Policy"), max_length=255, blank=True)
    minimum_order_quantity = models.PositiveIntegerField(_("Minimum Order Quantity"), default=1)

    # Meta info
    created_at = models.DateTimeField(_("Created At"))
    updated_at = models.DateTimeField(_("Updated At"))
    barcode = models.CharField(_("Barcode"), max_length=50)
    qr_code = models.ImageField(_("QR Code"), upload_to='products/qr_codes/', blank=True, null=True)

    thumbnail = models.ImageField(_("Thumbnail"), upload_to='products/thumbnails/', blank=True, null=True)

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    """Multiple images for a product."""
    product = models.ForeignKey(Product, verbose_name=_("Product"), related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(_("Image"), upload_to='products/product_images/', blank=True, null=True)
    image_order = models.PositiveSmallIntegerField(_("Image Order"), default=0)  # For ordering images

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        ordering = ['image_order']

    def __str__(self):
        return f"Image {self.image_order + 1} for {self.product.title}"


class ProductReview(models.Model):
    """Customer reviews for a product."""
    product = models.ForeignKey(Product, verbose_name=_("Product"), related_name="reviews", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(_("Rating"))
    comment = models.TextField(_("Comment"))
    date = models.DateTimeField(_("Date"), auto_now_add=True)
    reviewer_name = models.CharField(_("Reviewer Name"), max_length=100)
    reviewer_email = models.EmailField(_("Reviewer Email"))

    class Meta:
        verbose_name = _("Product Review")
        verbose_name_plural = _("Product Reviews")

    def __str__(self):
        return f"Review by {self.reviewer_name} ({self.rating}★)"
    

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), null=True, blank=True, on_delete=models.CASCADE)
    products = models.ManyToManyField('Product', verbose_name=_("Products"), blank=True)
    updated = models.DateTimeField(_("Updated"), auto_now_add=False, auto_now=True)
    active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")

    def __str__(self):
        return f"Cart ID {str(self.id)}"

    def get_total(self):
        # assuming Product model has a 'price' field
        return sum(p.price for p in self.products.all())

class Slider(models.Model):
    image = models.ImageField(_("Image"), upload_to='ImageSlider/')
    title = models.CharField(_("Title"), max_length=100)

    class Meta:
        verbose_name = _("Slider")
        verbose_name_plural = _("Sliders")

    def __str__(self):
        return self.title

class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE)
    street_address = models.CharField(_("Street Address"), max_length=100)
    apartment_address = models.CharField(_("Apartment Address"), max_length=100)
    country = CountryField(_("Country"), multiple=False)
    zip = models.CharField(_("ZIP Code"), max_length=100)

    class Meta:
        verbose_name = _("Billing Address")
        verbose_name_plural = _("Billing Addresses")

    def __str__(self):
        return self.user.username

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE)
    amount = models.FloatField(_("Amount"))
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    payment_method = models.CharField(_("Payment Method"), max_length=100)
    charge_id = models.CharField(_("Charge ID"), max_length=50)
    success = models.BooleanField(_("Success"), default=False)

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self):
        return f"Payment: {self.charge_id} - {self.amount}"

class Coupon(models.Model):
    code = models.CharField(_("Code"), max_length=15, unique=True)
    amount = models.FloatField(_("Amount"))

    class Meta:
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")

    def __str__(self):
        return self.code

class Refund(models.Model):
    order = models.ForeignKey('Order', verbose_name=_("Order"), on_delete=models.CASCADE)
    reason = models.TextField(_("Reason"))
    accepted = models.BooleanField(_("Accepted"), default=False)
    email = models.EmailField(_("Email"))

    class Meta:
        verbose_name = _("Refund")
        verbose_name_plural = _("Refunds")

    def __str__(self):
        return f"Refund for Order: {self.order}"

class ContactMessage(models.Model):
    email = models.EmailField(_("Email"))
    subject = models.CharField(_("Subject"), max_length=255)
    details = models.TextField(_("Details"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    status = models.CharField(_("Status"), max_length=20, default="Pending", choices=[("Pending", _("Pending")), ("Resolved", _("Resolved"))])

    class Meta:
        verbose_name = _("Contact Message")
        verbose_name_plural = _("Contact Messages")

    def __str__(self):
        return f"Message from {self.email}"


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE, related_name='orders')
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    phone_number = models.CharField(_("Phone Number"), max_length=20, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message=_("Phone number must be entered in the format: '+999999999'."))])
    district = models.CharField(_("District"), max_length=100)
    upozila = models.CharField(_("Upazila"), max_length=100)
    city = models.CharField(_("City"), max_length=100, blank=False, null=False)
    address = models.TextField(_("Address"))
    
    payment_method = models.CharField(_("Payment Method"), max_length=50)
    phone_number_payment = models.CharField(_("Phone Number for Payment"), max_length=20, blank=False, null=False)
    transaction_id = models.CharField(_("Transaction ID"), max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    ordered = models.BooleanField(_("Ordered"), default=False)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return f"Order {self.id} - {self.first_name} {self.last_name}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.order_items.all()) + 80  # Assuming 80 is the delivery charge
    
class OrderItem(models.Model):
    order = models.ForeignKey('Order', verbose_name=_("Order"), on_delete=models.CASCADE, related_name='order_items')
    product = models.CharField(_("Product"), max_length=100)
    quantity = models.PositiveIntegerField(_("Quantity"))
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    color = models.CharField(_("Color"), max_length=50, blank=False, null=False)
    size = models.CharField(_("Size"), max_length=50, blank=False, null=False)

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product} in Order {self.order.id}"
    

class HeroSection(models.Model):
    title = models.CharField(_("Title"), max_length=255)
    offer = models.CharField(_("Offer"), max_length=255)
    button_1_Text = models.CharField(_("Button 1 Text"), max_length=20)
    button_1_navigate_url = models.URLField(_("Button 1 Navigate URL"), max_length=2000, default="")
    button_2_Text = models.CharField(_("Button 2 Text"), max_length=20)
    button_2_navigate_url = models.URLField(_("Button 2 Navigate URL"), max_length=2000, default="")
    image = models.ImageField(_("Image"), upload_to='HeroSection/')

    class Meta:
        verbose_name = _("Hero Section")
        verbose_name_plural = _("Hero Sections")

    def __str__(self):
        return self.title


class TopSellingProducts(models.Model):
    product = models.ForeignKey('Product', verbose_name=_("Product"), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Top Selling Product")
        verbose_name_plural = _("Top Selling Products")
        unique_together = ['product']  # Ensure a product can only be added once

    def __str__(self):
        return f"Top Selling Product: {self.product.title}"
    
    @property
    def discounted_price(self):
        """Calculate the discounted price of the product"""
        if self.product.discount_percentage > 0:
            discount_amount = (self.product.price * self.product.discount_percentage) / 100
            return self.product.price - discount_amount
        return self.product.price
    
    @property
    def is_available(self):
        """Check if the product is available"""
        return self.product.stock > 0 and self.product.availability_status.lower() == 'in stock'
    
    @property
    def savings_amount(self):
        """Calculate the savings amount due to discount"""
        if self.product.discount_percentage > 0:
            return (self.product.price * self.product.discount_percentage) / 100
        return 0

class TopCategory(models.Model):
    category = models.ForeignKey('Category', verbose_name=_("Category"), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Top Category")
        verbose_name_plural = _("Top Categories")
        unique_together = ['category']  # Ensure a category can only be added once

    def __str__(self):
        return f"Top Category: {self.category.name}"
    
    @property
    def category_product_count(self):
        """Get the total number of products in this category"""
        return self.category.product_count
    
    @property
    def is_active(self):
        """Check if the category is active"""
        return self.category.is_active
    
    @property
    def category_image(self):
        """Get the category image"""
        return self.category.image
    
    @property
    def category_description(self):
        """Get the category description"""
        return self.category.description