from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AddToCartView, CartListView, ContactMessageCreateView, DistrictsViewSet, CategoryViewSet, HeroSectionViewSet, 
    ItemTypeViewSet, ProductDetailView, RemoveFromCartView,SizeViewSet, RatingViewSet, 
    ColorViewSet, ItemViewSet, ItemImageViewSet,ItemSizeViewSet, ItemColorViewSet, OrderViewSet, 
    SliderViewSet, BillingAddressViewSet, PaymentViewSet, CouponViewSet, RefundViewSet, 
    UpdateCartQuantityView, get_item_by_product_id, OrderViewSet, OrderItemViewSet, UserOrderList
)

router = DefaultRouter()
router.register(r'districts', DistrictsViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'item-types', ItemTypeViewSet)
router.register(r'sizes', SizeViewSet)
router.register(r'ratings', RatingViewSet)
router.register(r'colors', ColorViewSet)
router.register(r'items', ItemViewSet)
router.register(r'item-images', ItemImageViewSet)
router.register(r'item-sizes', ItemSizeViewSet)
router.register(r'item-colors', ItemColorViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'sliders', SliderViewSet)
router.register(r'billing-addresses', BillingAddressViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'coupons', CouponViewSet)
router.register(r'refunds', RefundViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'hero-sections', HeroSectionViewSet) 

# Custom route for fetching a single product by product_id
urlpatterns = [
    path('', include(router.urls)),
    
    path('items/<str:product_id>/', get_item_by_product_id, name='item-by-product-id'),
    # path('user-orders/', UserOrderList.as_view(), name='user-order-list'),

    path('cart/', CartListView.as_view(), name='cart-list'),
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/remove/<str:pk>/', RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('product/<int:id>/', ProductDetailView.as_view(), name='product-detail'),  
    path('cart/update/<int:pk>/', UpdateCartQuantityView.as_view(), name='update-cart'),
    
    path('contact/', ContactMessageCreateView.as_view(), name='contact-message'),
]
