
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from .models import ( BillingAddress, Cart, Category, Color, 
                     ContactMessage, Coupon, Districts, HeroSection, 
                     Item, ItemColor, ItemImage, ItemSize, ItemType, Order, 
                     OrderItem, Payment, Rating, Refund, Size, Slider,
)

from .serializers import (
    ItemSerilizers, ItemImageSerilizers, ItemSizeSerilizers, ItemColorSerilizers,
    CategorySerilizers, ItemTypeSerilizers, HeroSectionSerilizers, 
    DistrictsSerilizers, ContactMessageSerilizers, SliderSerilizers,
    BillingAddressSerilizers, PaymentSerilizers, CouponSerilizers, RefundSerilizers,
    CartSerilizers, OrderSerilizers, OrderItemSerilizers, RatingSerilizers, 
    SizeSerilizers, ColorSerilizers
)

class ItemViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ItemSerilizers

    def get_queryset(self):
        queryset = Item.objects.select_related(
            "ratings",
            "category",
            "type",
        ).prefetch_related(
            "images",
            "item_size__size",
            "item_color__color",
        )

        limit = self.request.query_params.get('limit', None)
        if limit is not None:
            try:
                queryset = queryset[:int(limit)]
            except (ValueError, TypeError):
                pass

        return queryset

class ItemDetailViews(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ItemSerilizers
    queryset = Item.objects.select_related(
        "ratings",
        "category",
        "type",
    ).prefetch_related(
        "images",
        "item_size__size",
        "item_color__color",
    )

class ItemImageViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ItemImageSerilizers
    queryset = ItemImage.objects.all()
    
class ItemSizeViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ItemSizeSerilizers
    queryset = ItemSize.objects.all()
    
class ItemColorViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ItemColorSerilizers
    queryset = ItemColor.objects.all()
    
class CategoryViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerilizers
    queryset = Category.objects.all()
    
class ItemTypeViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ItemTypeSerilizers
    queryset = ItemType.objects.all()
    
class HeroSectionViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = HeroSectionSerilizers
    queryset = HeroSection.objects.all()
    
class DistrictsViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = DistrictsSerilizers
    queryset = Districts.objects.all()
    
class ContactMessageViews(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ContactMessageSerilizers
    queryset = ContactMessage.objects.all()
    
    
class SliderViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SliderSerilizers
    queryset = Slider.objects.all()
    
class BillingAddressViews(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BillingAddressSerilizers
    queryset = BillingAddress.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
class PaymentViews(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerilizers
    queryset = Payment.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
class CouponViews(generics.CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = CouponSerilizers
    queryset = Coupon.objects.all()


class RefundViews(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RefundSerilizers
    queryset = Refund.objects.all()


class RatingViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = RatingSerilizers
    queryset = Rating.objects.all()


class SizeViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SizeSerilizers
    queryset = Size.objects.all()


class ColorViews(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ColorSerilizers
    queryset = Color.objects.all()


class CartViews(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerilizers
    queryset = Cart.objects.all()

    def get_queryset(self):
        return Cart.objects.filter(user_name=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user_name=self.request.user)


class OrderViews(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerilizers
    queryset = Order.objects.all()

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderItemViews(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderItemSerilizers
    queryset = OrderItem.objects.all()
    