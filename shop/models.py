from django.conf import settings
from django.db import models
from uuid import uuid4
from django.utils import timezone
from django.shortcuts import reverse
from django.contrib.auth.models import User
from django_countries.fields import CountryField
from django.core.validators import RegexValidator
    
from django.contrib.auth import get_user_model

User = settings.AUTH_USER_MODEL

class Districts(models.Model):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

## THIS CHANGE FOR 'dummy' PRODUCTS
class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    stock = models.PositiveIntegerField()
    tags = models.JSONField(default=list, blank=True)  # List of strings
    brand = models.CharField(max_length=100)
    sku = models.CharField(max_length=100, unique=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2)

    # Dimensions
    width = models.DecimalField(max_digits=10, decimal_places=2)
    height = models.DecimalField(max_digits=10, decimal_places=2)
    depth = models.DecimalField(max_digits=10, decimal_places=2)

    warranty_information = models.CharField(max_length=255, blank=True)
    shipping_information = models.CharField(max_length=255, blank=True)
    availability_status = models.CharField(max_length=50)

    # Policies
    return_policy = models.CharField(max_length=255, blank=True)
    minimum_order_quantity = models.PositiveIntegerField(default=1)

    # Meta info
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    barcode = models.CharField(max_length=50)
    qr_code = models.ImageField(upload_to='products/qr_codes/', blank=True, null=True)

    thumbnail = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    """Multiple images for a product."""
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/product_images/', blank=True, null=True)
    image_order = models.PositiveSmallIntegerField(default=0)  # For ordering images

    class Meta:
        ordering = ['image_order']

    def __str__(self):
        return f"Image {self.image_order + 1} for {self.product.title}"


class ProductReview(models.Model):
    """Customer reviews for a product."""
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    date = models.DateTimeField()
    reviewer_name = models.CharField(max_length=100)
    reviewer_email = models.EmailField()

    def __str__(self):
        return f"Review by {self.reviewer_name} ({self.rating}★)"

    
class Slider(models.Model):
    image = models.ImageField(upload_to='images/slider')
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=100)
    charge_id = models.CharField(max_length=50)
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment: {self.charge_id} - {self.amount}"

class Coupon(models.Model):
    code = models.CharField(max_length=15, unique=True)
    amount = models.FloatField()

    def __str__(self):
        return self.code

class Refund(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"Refund for Order: {self.order}"


## this Changes for 'dummy' PRODUCTS API
class Cart(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    discountPercentage = models.DecimalField(max_digits=5, decimal_places=2)
    discountedTotal = models.DecimalField(max_digits=10, decimal_places=2)
    thumbnail = models.ImageField(upload_to='imagess/cart/thumbnails/', blank=True, null=True)

class ContactMessage(models.Model):
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pending", choices=[("Pending", "Pending"), ("Resolved", "Resolved")])

    def __str__(self):
        return f"Message from {self.email}"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'.")])
    district = models.CharField(max_length=100)
    upozila = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=False, null=False)
    address = models.TextField()
    
    payment_method = models.CharField(max_length=50)
    phone_number_payment = models.CharField(max_length=20, blank=False, null=False)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ordered = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} - {self.first_name} {self.last_name}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.order_items.all()) + 80  # Assuming 80 is the delivery charge
    
class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items')
    product = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=50, blank=False, null=False)
    size = models.CharField(max_length=50, blank=False, null=False)

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product} in Order {self.order.id}"
    

class HeroSection(models.Model):
    title = models.CharField(max_length=255)
    offer = models.CharField(max_length=255)
    button_1_Text = models.CharField(max_length=20)
    button_2_Text = models.CharField(max_length=20)
    image = models.ImageField(upload_to='HeroSection/')
