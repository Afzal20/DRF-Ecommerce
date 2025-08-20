from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ContactMessageCreateView, DistrictsViewSet, HeroSectionViewSet, 
    ProductDetailView, OrderViewSet, OrderItemViewSet, CartAPIView,
    SliderViewSet, BillingAddressViewSet, PaymentViewSet, CouponViewSet, RefundViewSet, TopSellingProductsViewSet, 
    TopCategoryViewSet, get_product_by_id, UserOrderList, ProductViewSet, ProductImageViewSet, ProductReviewViewSet,
    CategoryViewSet, featured_categories, category_products,  # Added Category views
)

router = DefaultRouter()
router.register(r'districts', DistrictsViewSet)
router.register(r'categories', CategoryViewSet)  
router.register(r'products', ProductViewSet)
router.register(r'product-images', ProductImageViewSet)
router.register(r'product-reviews', ProductReviewViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'sliders', SliderViewSet)
router.register(r'billing-addresses', BillingAddressViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'coupons', CouponViewSet)
router.register(r'refunds', RefundViewSet)
router.register(r'hero-sections', HeroSectionViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # Custom routes
    path('products/<int:product_id>/', get_product_by_id, name='product-by-id'),
    path('top-selling-products/', TopSellingProductsViewSet.as_view({'get': 'list'}), name='top-selling-products'),
    path('top-categories/', TopCategoryViewSet.as_view({'get': 'list'}), name='top-categories'),

    # Category-specific endpoints
    path('categories/featured/', featured_categories, name='featured-categories'),
    path('categories/<slug:slug>/products/', category_products, name='category-products'),

    # Contact form
    path('contact/', ContactMessageCreateView.as_view(), name='contact-message'),

    # Cart API (token + session based)
    path('cart/', CartAPIView.as_view(), name='cart'),
]
