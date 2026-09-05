from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from .models import (
    BillingAddress,
    Cart,
    Category,
    Color,
    ContactMessage,
    Coupon,
    Districts,
    HeroSection,
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
)
from .permissions import IsOwner
from .serializers import (
    BillingAddressSerilizers,
    CartSerilizers,
    CategorySerilizers,
    ColorSerilizers,
    ContactMessageSerilizers,
    CouponSerilizers,
    DistrictsSerilizers,
    HeroSectionSerilizers,
    ItemColorSerilizers,
    ItemImageSerilizers,
    ItemSerilizers,
    ItemSizeSerilizers,
    ItemTypeSerilizers,
    OrderItemSerilizers,
    OrderSerilizers,
    PaymentSerilizers,
    RatingSerilizers,
    RefundSerilizers,
    SizeSerilizers,
    SliderSerilizers,
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

        category = self.request.query_params.get("category", None)
        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=int(category))
            else:
                queryset = queryset.filter(category__name__iexact=category)

        limit = self.request.query_params.get("limit", None)
        if limit is not None:
            try:
                queryset = queryset[: int(limit)]
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


class BillingAddressViews(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = BillingAddressSerilizers

    def get_queryset(self):
        return BillingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentViews(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = PaymentSerilizers

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CouponViews(generics.CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = CouponSerilizers
    queryset = Coupon.objects.all()


class RefundViews(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = RefundSerilizers

    def get_queryset(self):
        return Refund.objects.filter(order__user=self.request.user)


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
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = CartSerilizers

    def get_queryset(self):
        return Cart.objects.filter(user_name=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user_name=self.request.user)


class CartItemViews(generics.RetrieveUpdateDestroyAPIView):
    """
    Detail view for a single cart line item (retrieve / update quantity / delete).
    Used by the storefront to remove items after checkout and to update quantities.
    """

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = CartSerilizers

    def get_queryset(self):
        return Cart.objects.filter(user_name=self.request.user)


class OrderViews(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = OrderSerilizers

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderItemViews(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = OrderItemSerilizers

    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user)
