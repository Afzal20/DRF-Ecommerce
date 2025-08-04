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
from .models import Cart, ContactMessage, HeroSection
from .serializers import CartSerializer, AddToCartSerializer, ContactMessageSerializer, HeroSectionSerializer
from rest_framework import generics
from .serializers import ProductSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import (
    Districts, Category, ItemType, Size, Rating, Color,
    Item, ItemImage, ItemSize, ItemColor, Cart, Order,
    Slider, BillingAddress, Payment, Coupon, Refund
)
from .serializers import (
    AddToCartSerializer, DistrictsSerializer, CategorySerializer, ItemTypeSerializer,
    SizeSerializer, RatingSerializer, ColorSerializer, ItemSerializer,
    ItemImageSerializer, ItemSizeSerializer, ItemColorSerializer, CartSerializer,
    OrderSerializer, SliderSerializer, BillingAddressSerializer,
    PaymentSerializer, CouponSerializer, RefundSerializer
)

from rest_framework import generics, viewsets
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from django.contrib.auth import get_user_model

from django.http import HttpResponse, Http404
import os
import mimetypes
from django.conf import settings

# ModelViewSets for the basic CRUD operations

class DistrictsViewSet(viewsets.ModelViewSet):
    queryset = Districts.objects.all()
    serializer_class = DistrictsSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ItemTypeViewSet(viewsets.ModelViewSet):
    queryset = ItemType.objects.all()
    serializer_class = ItemTypeSerializer

class SizeViewSet(viewsets.ModelViewSet):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

class ColorViewSet(viewsets.ModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    lookup_field = 'product_id'  # Use product_id instead of the default 'id'
    
    lookup_value_regex = '[\w-]+'

class ItemImageViewSet(viewsets.ModelViewSet):
    queryset = ItemImage.objects.all()
    serializer_class = ItemImageSerializer

class ItemSizeViewSet(viewsets.ModelViewSet):
    queryset = ItemSize.objects.all()
    serializer_class = ItemSizeSerializer

class ItemColorViewSet(viewsets.ModelViewSet):
    queryset = ItemColor.objects.all()
    serializer_class = ItemColorSerializer 

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()  # <-- Add this line

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        return Order.objects.none()

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

@api_view(['GET'])
def get_item_by_product_id(request, product_id):
    try:
        # Fetch the item by product_id
        item = Item.objects.prefetch_related('images', 'item_size__size', 'item_color__color').filter(product_id=product_id).first()

        if item:
            # Serialize the item using the ItemSerializer
            serializer = ItemSerializer(item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddToCartSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CartListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user_name=self.request.user, ordered=False)
        return Cart.objects.none()

class RemoveFromCartView(DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user_name=self.request.user, ordered=False)
        return Cart.objects.none()

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Item.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id' 
    
    def get(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product)
        return Response(serializer.data)


class UpdateCartQuantityView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk, *args, **kwargs):
        try:
            cart_item = Cart.objects.get(pk=pk, user_name=request.user, ordered=False)
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

class OrderItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer
    
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

class UserOrderList(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        return Order.objects.none()
    

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


class HeroSectionViewSet(viewsets.ModelViewSet):
    queryset = HeroSection.objects.all()
    serializer_class = HeroSectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return HeroSection.objects.all()

def index(request):
    return render(request, 'index.html')