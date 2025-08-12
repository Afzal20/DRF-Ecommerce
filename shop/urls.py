from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AddToCartView, CartListView, ContactMessageCreateView, DistrictsViewSet, HeroSectionViewSet, 
    ProductDetailView, RemoveFromCartView, OrderViewSet, OrderItemViewSet, CartViewSet,
    SliderViewSet, BillingAddressViewSet, PaymentViewSet, CouponViewSet, RefundViewSet, TopSellingProductsViewSet, 
    TopCategoryViewSet, UpdateCartQuantityView, get_product_by_id, UserOrderList, ProductViewSet, ProductImageViewSet, ProductReviewViewSet,
    CategoryViewSet, featured_categories, category_products,  # Added Category views
)

router = DefaultRouter()
router.register(r'districts', DistrictsViewSet)
router.register(r'categories', CategoryViewSet)  # Added categories endpoint
router.register(r'products', ProductViewSet)
router.register(r'product-images', ProductImageViewSet)
router.register(r'product-reviews', ProductReviewViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'cart', CartViewSet)
router.register(r'sliders', SliderViewSet)
router.register(r'billing-addresses', BillingAddressViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'coupons', CouponViewSet)
router.register(r'refunds', RefundViewSet)
router.register(r'hero-sections', HeroSectionViewSet) 

# Custom route for fetching a single product by product_id
urlpatterns = [
    path('', include(router.urls)),
    
    path('products/<int:product_id>/', get_product_by_id, name='product-by-id'),
    path('top-selling-products/', TopSellingProductsViewSet.as_view({'get': 'list'}), name='top-selling-products'),
    path('top-categories/', TopCategoryViewSet.as_view({'get': 'list'}), name='top-categories'),

    # Category-specific endpoints
    path('categories/featured/', featured_categories, name='featured-categories'),
    path('categories/<slug:slug>/products/', category_products, name='category-products'),

    path('cart/', CartListView.as_view(), name='cart-list'),
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/remove/<str:pk>/', RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('product/<int:id>/', ProductDetailView.as_view(), name='product-detail'),  
    path('cart/update/<int:pk>/', UpdateCartQuantityView.as_view(), name='update-cart'),
    
    path('contact/', ContactMessageCreateView.as_view(), name='contact-message'),
]
