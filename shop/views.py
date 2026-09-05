from django.db.models import Q
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
    NewArrivalBannerImageSerializer,
    NewArrivalBannerSerializer,
    OrderItemSerilizers,
    OrderSerilizers,
    PaymentSerilizers,
    RatingSerilizers,
    RefundSerilizers,
    SiteSettingSerializer,
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

        is_featured = self.request.query_params.get("is_featured", None)
        if is_featured is not None:
            if is_featured.lower() in ["true", "1"]:
                queryset = queryset.filter(is_featured=True)
            elif is_featured.lower() in ["false", "0"]:
                queryset = queryset.filter(is_featured=False)

        is_bestselling = self.request.query_params.get("is_bestselling", None)
        if is_bestselling is not None:
            if is_bestselling.lower() in ["true", "1"]:
                queryset = queryset.filter(is_bestselling=True)
            elif is_bestselling.lower() in ["false", "0"]:
                queryset = queryset.filter(is_bestselling=False)

        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(brand_name__icontains=search)
            )

        min_price = self.request.query_params.get("min_price", None)
        if min_price is not None:
            try:
                queryset = queryset.filter(price__gte=int(min_price))
            except (ValueError, TypeError):
                pass

        max_price = self.request.query_params.get("max_price", None)
        if max_price is not None:
            try:
                queryset = queryset.filter(price__lte=int(max_price))
            except (ValueError, TypeError):
                pass

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


class NewArrivalBannerView(generics.RetrieveAPIView):
    """
    Returns the active New Arrivals Banner with its active images.
    Auto-initializes the default banner and image if none exist.
    """

    permission_classes = [AllowAny]
    serializer_class = NewArrivalBannerSerializer

    def get_object(self):
        banner = NewArrivalBanner.objects.filter(is_active=True).first()
        if not banner:
            banner, _ = NewArrivalBanner.objects.get_or_create(
                id=1,
                defaults={
                    "title": "NEW ARRIVALS",
                    "subtitle": "Curabitur luctus ipsum eget convallis",
                    "discount_percent": "50%",
                    "discount_text": "ON ALL PRODUCTS",
                    "is_active": True,
                },
            )
            if not banner.images.exists():
                NewArrivalBannerImage.objects.create(
                    banner=banner,
                    image_name="Modern Tablet and Gadget Showcase",
                    image_url="https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?q=80&w=2027&auto=format&fit=crop",
                    order=0,
                    is_active=True,
                )
        return banner


class NewArrivalBannerImageListView(generics.ListAPIView):
    """
    Returns all active images for the New Arrivals Banner.
    """

    permission_classes = [AllowAny]
    serializer_class = NewArrivalBannerImageSerializer

    def get_queryset(self):
        return NewArrivalBannerImage.objects.filter(is_active=True).order_by(
            "order", "id"
        )


class SiteSettingView(generics.RetrieveAPIView):
    """
    Returns active site settings (hotline, site name, announcement).
    Auto-initializes defaults if none exist in the database.
    """

    permission_classes = [AllowAny]
    serializer_class = SiteSettingSerializer

    def get_object(self):
        setting = SiteSetting.objects.filter(is_active=True).first()
        if not setting:
            setting, _ = SiteSetting.objects.get_or_create(
                id=1,
                defaults={
                    "site_name": "MAXSHOP",
                    "hotline_label": "HOTLINE:",
                    "hotline_number": "(801) 2345 - 6789",
                    "announcement_badge": "This Week",
                    "announcement_text": "Maecenas faucibus mollis",
                    "is_active": True,
                },
            )
        return setting
