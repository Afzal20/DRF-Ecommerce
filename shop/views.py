from django.shortcuts import render
import jwt
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, DestroyAPIView

from decimal import Decimal

from .models import (
    Cart, CartItem, ContactMessage, HeroSection, Districts, Order, OrderItem,
    Slider, BillingAddress, Payment, Coupon, Refund, Product, ProductImage, ProductReview, TopSellingProducts,
    TopCategory,
    Category,  # Added Category import
)
from .serializers import (
    CartItemSerializer, CartSerializer, ContactMessageSerializer, HeroSectionSerializer,
    DistrictsSerializer, OrderSerializer, OrderItemSerializer, SliderSerializer, 
    BillingAddressSerializer, PaymentSerializer, CouponSerializer, RefundSerializer,
    ProductSerializer, ProductImageSerializer, ProductReviewSerializer, TopSellingProductsSerializer,
    TopSellingProductsSimpleSerializer, TopCategorySerializer, TopCategorySimpleSerializer,
    CategorySerializer, CategoryListSerializer,  # Added Category serializers
)
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.contrib.auth import get_user_model

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from django.http import HttpResponse, Http404, HttpResponseNotModified

import os
import mimetypes
from django.conf import settings

# ModelViewSets for the basic CRUD operations

class DistrictsViewSet(viewsets.ModelViewSet):
    queryset = Districts.objects.all()
    serializer_class = DistrictsSerializer
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @method_decorator(cache_page(60 * 60 * 2, key_prefix='product_list'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        return Order.objects.none()

class OrderItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

class SliderViewSet(viewsets.ModelViewSet):
    queryset = Slider.objects.all()
    serializer_class = SliderSerializer

    @method_decorator(cache_page(60 * 60 * 2, key_prefix='slider_list'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class BillingAddressViewSet(viewsets.ModelViewSet):
    queryset = BillingAddress.objects.all()
    serializer_class = BillingAddressSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

class RefundViewSet(viewsets.ModelViewSet):
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer


class ContactMessageCreateView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Message sent successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserOrderList(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        return Order.objects.none()

class HeroSectionViewSet(viewsets.ModelViewSet):
    queryset = HeroSection.objects.all()
    serializer_class = HeroSectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

@api_view(['GET'])
def get_product_by_id(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'
    

def serve_media(request, path):
    media_path = os.path.join(settings.MEDIA_ROOT, path)

    if os.path.exists(media_path):
        with open(media_path, 'rb') as f:
            mime_type, _ = mimetypes.guess_type(media_path)
            response = HttpResponse(f.read(), content_type=mime_type or 'application/octet-stream')
            response["Content-Disposition"] = f'inline; filename="{os.path.basename(media_path)}"'
                
            return response
    else:
        raise Http404("Media file not found")

def index(request):
    return render(request, 'index.html')


class TopSellingProductsViewSet(viewsets.ModelViewSet):
    queryset = TopSellingProducts.objects.select_related('product').all()
    serializer_class = TopSellingProductsSerializer

    @method_decorator(cache_page(60 * 60 * 2, key_prefix='top_selling_products'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """Optimize queries by selecting related product data"""
        return TopSellingProducts.objects.select_related(
            'product'
        ).prefetch_related(
            'product__images', 
            'product__reviews'
        )
    
    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'list':
            # Use the regular serializer for now - can be optimized later
            return TopSellingProductsSerializer
        return TopSellingProductsSerializer


class TopCategoryViewSet(viewsets.ModelViewSet):
    queryset = TopCategory.objects.select_related('category').all()
    serializer_class = TopCategorySerializer

    @method_decorator(cache_page(60 * 60 * 2, key_prefix='top_categories'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """Optimize queries by selecting related category data"""
        return TopCategory.objects.select_related('category').filter(category__is_active=True)
    
    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'list':
            # Use the regular serializer for now - can be optimized later
            return TopCategorySerializer
        return TopCategorySerializer


# Category ViewSets
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories.
    Provides full CRUD operations for categories.
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'  # Allow lookup by slug for SEO-friendly URLs

    def get_serializer_class(self):
        """Use simplified serializer for list view"""
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer

    @method_decorator(cache_page(60 * 60 * 1, key_prefix='category_list'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """Filter categories and optionally return only featured ones"""
        queryset = Category.objects.filter(is_active=True)
        
        # Featured functionality is not available in the current Category model
        # If you need featured categories, add is_featured field to Category model
        
        return queryset.order_by('sort_order', 'name')


@api_view(['GET'])
@cache_page(60 * 60 * 2, key_prefix='featured_categories')  # Cache for 2 hours
def featured_categories(request):
    """
    API endpoint to get featured categories for the homepage.
    """
    categories = Category.objects.filter(is_active=True).order_by('sort_order', 'name')
    serializer = CategoryListSerializer(categories, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@cache_page(60 * 60 * 1, key_prefix='category_products')  # Cache for 1 hour
def category_products(request, slug):
    """
    API endpoint to get products by category slug.
    Optimized with caching and efficient queries.
    """
    try:
        # Optimize category query
        category = Category.objects.get(slug=slug, is_active=True)
        
        # Optimize products query with select_related and prefetch_related
        products = Product.objects.filter(
            category=category
        ).select_related(
            'category'
        ).prefetch_related(
            'images', 
            'reviews'
        )
        
        # Handle pagination parameters
        page_size = request.query_params.get('page_size', 20)
        page = request.query_params.get('page', 1)
        
        try:
            page_size = int(page_size)
            page = int(page)
            if page_size > 100:  # Limit max page size
                page_size = 100
            if page < 1:
                page = 1
        except ValueError:
            page_size = 20
            page = 1
            
        # Calculate pagination
        total_products = products.count()
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_products = products[start_index:end_index]
        
        # Serialize data
        serializer = ProductSerializer(paginated_products, many=True, context={'request': request})
        
        return Response({
            'category': CategorySerializer(category, context={'request': request}).data,
            'products': serializer.data,
            'total_products': total_products,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_products + page_size - 1) // page_size,
            'has_next': end_index < total_products,
            'has_previous': page > 1
        })
        
    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    
class CartTokenMixin:
    token_param = "token"
    token = None

    def get_cart_from_token(self):
        """
        Reads token from request (query param or body) and returns
        (data, cart_instance, response_status).
        """
        token = (
            self.request.query_params.get(self.token_param)
            or self.request.data.get(self.token_param)
        )
        self.token = token

        if not token:
            return None, None, status.HTTP_400_BAD_REQUEST

        try:
            data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            cart_id = data.get("cart_id")
        except Exception:
            return None, None, status.HTTP_400_BAD_REQUEST

        from .models import Cart
        try:
            cart_obj = Cart.objects.get(id=cart_id, active=True)
        except Cart.DoesNotExist:
            return None, None, status.HTTP_404_NOT_FOUND

        return data, cart_obj, status.HTTP_200_OK

    def create_token(self, data):
        """
        Creates a signed JWT with cart_id
        """
        token = jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")
        self.token = token
        return token


class CartUpdateAPIMixin:
    def update_cart(self):
        cart = self.cart or getattr(self, "cart", None)
        if not cart:
            return None

        subtotal = Decimal('0.00')
        for item in cart.cartitem_set.all():
            subtotal += item.line_item_total

        cart.subtotal = subtotal
        cart.tax_total = cart.subtotal * cart.tax_percentage
        cart.total = cart.subtotal + cart.tax_total
        cart.save()

        return cart



class CartAPIView(CartTokenMixin, CartUpdateAPIMixin, APIView):
    serializer_class = CartSerializer
    token_param = "token"
    cart = None

    def get_cart(self):
        data, cart_obj, response_status = self.get_cart_from_token()
        if cart_obj == None or not cart_obj.active:
            cart = Cart()
            cart.tax_percentage = Decimal('0.075')  # Use Decimal instead of float
            if self.request.user.is_authenticated:
                cart.user = self.request.user
            cart.save()
            data = {
                "cart_id": str(cart.id)
            }
            self.create_token(data)
            cart_obj = cart

        return cart_obj

    def get(self, request, format=None):
        cart = self.get_cart()
        self.cart = cart
        self.update_cart()
        items = CartItemSerializer(cart.cartitem_set.all(), many=True, context={'request': request})
        
        data = {
            "token": self.token,
            "cart": cart.id,
            "total": cart.total,
            "subtotal": cart.subtotal,
            "tax_total": cart.tax_total,
            "count": cart.cartitem_set.count(),
            "items": items.data,
        }
        return Response(data)

    def post(self, request, format=None):
        # Get cart using token-based authentication (consistent with GET)
        cart = self.get_cart()
        self.cart = cart
        
        product_id = request.data.get('product_id', None)
        quantity = int(request.data.get('quantity', 1))
        
        if product_id is not None:
            try:
                product_obj = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product does not exist."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                item=product_obj,
                defaults={
                    'quantity': quantity,
                    'line_item_total': Decimal(str(product_obj.price)) * Decimal(str(quantity))
                }
            )
            
            if not created:
                # Update existing item
                cart_item.quantity += quantity
                cart_item.line_item_total = Decimal(str(product_obj.price)) * Decimal(str(cart_item.quantity))
                cart_item.save()
                added = False
            else:
                added = True
            
            # Update cart totals
            self.update_cart()
            
            # Get updated items for response
            items = CartItemSerializer(cart.cartitem_set.all(), many=True, context={'request': request})
            
            data = {
                "token": self.token,
                "cart": cart.id,
                "added": added,
                "updated": not added,
                "total": cart.total,
                "subtotal": cart.subtotal,
                "tax_total": cart.tax_total,
                "count": cart.cartitem_set.count(),
                "items": items.data,
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No product_id provided."}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, format=None):
        """Update cart item quantity"""
        cart = self.get_cart()
        self.cart = cart
        
        product_id = request.data.get('product_id', None)
        quantity = request.data.get('quantity', None)
        
        if product_id is None or quantity is None:
            return Response({"error": "product_id and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product_obj = Product.objects.get(id=product_id)
            cart_item = CartItem.objects.get(cart=cart, item=product_obj)
            
            if int(quantity) <= 0:
                cart_item.delete()
                removed = True
            else:
                cart_item.quantity = int(quantity)
                cart_item.line_item_total = Decimal(str(product_obj.price)) * Decimal(str(cart_item.quantity))
                cart_item.save()
                removed = False
            
            # Update cart totals
            self.update_cart()
            
            # Get updated items for response
            items = CartItemSerializer(cart.cartitem_set.all(), many=True, context={'request': request})
            
            data = {
                "token": self.token,
                "cart": cart.id,
                "removed": removed,
                "total": cart.total,
                "subtotal": cart.subtotal,
                "tax_total": cart.tax_total,
                "count": cart.cartitem_set.count(),
                "items": items.data,
            }
            return Response(data, status=status.HTTP_200_OK)
            
        except Product.DoesNotExist:
            return Response({"error": "Product does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, format=None):
        """Remove item from cart"""
        cart = self.get_cart()
        self.cart = cart
        
        product_id = request.data.get('product_id', None)
        
        if product_id is None:
            return Response({"error": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product_obj = Product.objects.get(id=product_id)
            cart_item = CartItem.objects.get(cart=cart, item=product_obj)
            cart_item.delete()
            
            # Update cart totals
            self.update_cart()
            
            # Get updated items for response
            items = CartItemSerializer(cart.cartitem_set.all(), many=True)
            
            data = {
                "token": self.token,
                "cart": cart.id,
                "removed": True,
                "total": cart.total,
                "subtotal": cart.subtotal,
                "tax_total": cart.tax_total,
                "count": cart.cartitem_set.count(),
                "items": items.data,
            }
            return Response(data, status=status.HTTP_200_OK)
            
        except Product.DoesNotExist:
            return Response({"error": "Product does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND)
