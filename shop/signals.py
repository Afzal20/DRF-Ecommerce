from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from shop.models import Product, TopSellingProducts, Category, ProductImage, ProductReview, TopCategory
from shop.utils.cache_utils import clear_cache_pattern

# Clear product cache 
@receiver(post_save, sender=Product)
def clear_product_cache_on_save(sender, instance, **kwargs):
    clear_cache_pattern("*product_list*")
    clear_cache_pattern("*category_products*")  # Clear category products cache too


@receiver(post_delete, sender=Product)
def clear_product_cache_on_delete(sender, instance, **kwargs):
    clear_cache_pattern("*product_list*")
    clear_cache_pattern("*category_products*")  # Clear category products cache too


# Clear product cache when ProductImage changes
@receiver(post_save, sender=ProductImage)
def clear_product_cache_on_image_save(sender, instance, **kwargs):
    clear_cache_pattern("*product_list*")
    clear_cache_pattern("*category_products*")


@receiver(post_delete, sender=ProductImage)
def clear_product_cache_on_image_delete(sender, instance, **kwargs):
    clear_cache_pattern("*product_list*")
    clear_cache_pattern("*category_products*")


# Clear product cache when ProductReview changes
@receiver(post_save, sender=ProductReview)
def clear_product_cache_on_review_save(sender, instance, **kwargs):
    clear_cache_pattern("*product_list*")
    clear_cache_pattern("*category_products*")


@receiver(post_delete, sender=ProductReview)
def clear_product_cache_on_review_delete(sender, instance, **kwargs):
    clear_cache_pattern("*product_list*")
    clear_cache_pattern("*category_products*")


# Clear category cache
@receiver(post_save, sender=Category)
def clear_category_cache_on_save(sender, instance, **kwargs):
    clear_cache_pattern("*category_list*")
    clear_cache_pattern("*featured_categories*")
    clear_cache_pattern("*category_products*")


@receiver(post_delete, sender=Category)
def clear_category_cache_on_delete(sender, instance, **kwargs):
    clear_cache_pattern("*category_list*")
    clear_cache_pattern("*featured_categories*")
    clear_cache_pattern("*category_products*")


# Clear top selling products cache
@receiver(post_save, sender=TopSellingProducts)
def clear_top_selling_products_cache_on_save(sender, instance, **kwargs):
    clear_cache_pattern("*top_selling_products*")


@receiver(post_delete, sender=TopSellingProducts)
def clear_top_selling_products_cache_on_delete(sender, instance, **kwargs):
    clear_cache_pattern("*top_selling_products*")


# Clear top categories cache
@receiver(post_save, sender=TopCategory)
def clear_top_categories_cache_on_save(sender, instance, **kwargs):
    clear_cache_pattern("*top_categories*")


@receiver(post_delete, sender=TopCategory)
def clear_top_categories_cache_on_delete(sender, instance, **kwargs):
    clear_cache_pattern("*top_categories*")


# Clear slider cache
@receiver(post_save, sender=TopCategory)
def clear_top_categories_cache_on_save(sender, instance, **kwargs):
    clear_cache_pattern("*slider_list*")


@receiver(post_delete, sender=TopCategory)
def clear_top_categories_cache_on_delete(sender, instance, **kwargs):
    clear_cache_pattern("*slider_list*")

