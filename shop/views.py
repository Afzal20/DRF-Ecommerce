from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, DestroyAPIView

import hashlib


from .models import (
    Cart, ContactMessage, HeroSection, Districts, Order, OrderItem,
    Slider, BillingAddress, Payment, Coupon, Refund, Product, ProductImage, ProductReview, TopSellingProducts,
    TopCategory,
    Category,  # Added Category import
)
from .serializers import (
    CartSerializer, AddToCartSerializer, ContactMessageSerializer, HeroSectionSerializer,
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


#Cache the list view response for 2 hours to improve performance.
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

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

class AddToCartView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CartListView(ListAPIView):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()

class RemoveFromCartView(DestroyAPIView):
    queryset = Cart.objects.all()
    
class UpdateCartQuantityView(APIView):
    def patch(self, request, pk, *args, **kwargs):
        try:
            cart_item = Cart.objects.get(pk=pk)
        except Cart.DoesNotExist:
            return Response({"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)

        quantity = request.data.get('quantity', None)
        if quantity is not None and int(quantity) > 0:
            cart_item.quantity = int(quantity)
            cart_item.save()
            return Response({"message": "Cart updated successfully"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)


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
            
            # Add cache headers for images (cache for 7 days)
            response['Cache-Control'] = 'public, max-age=604800'  # 7 days 60*60*24*7
            
            # Add ETag for better caching
            etag = hashlib.md5(f.read()).hexdigest()
            f.seek(0)  # Reset file pointer
            response['ETag'] = f'"{etag}"'
            
            # Check if client has cached version
            if request.META.get('HTTP_IF_NONE_MATCH') == f'"{etag}"':
                return HttpResponseNotModified()
                
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