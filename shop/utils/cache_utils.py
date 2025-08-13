"""
Utility functions for cache management
"""
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def clear_all_cache():
    """Clear all cache data"""
    try:
        cache.clear()
        logger.info("All cache cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False

def clear_cache_pattern(pattern):
    """Clear cache keys matching a pattern"""
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        keys = redis_conn.keys(pattern)
        if keys:
            redis_conn.delete(*keys)
            logger.info(f"Cleared {len(keys)} cache keys matching pattern: {pattern}")
            return len(keys)
        else:
            logger.info(f"No cache keys found matching pattern: {pattern}")
            return 0
    except Exception as e:
        logger.error(f"Error clearing cache pattern {pattern}: {str(e)}")
        return False

def clear_model_cache(model_name):
    """Clear cache for a specific model"""
    patterns = [
        f"*{model_name.lower()}*",
        f"*{model_name}*",
        f"views.decorators.cache.cache_*{model_name}*",
    ]
    
    total_cleared = 0
    for pattern in patterns:
        result = clear_cache_pattern(pattern)
        if isinstance(result, int):
            total_cleared += result
    
    logger.info(f"Cleared {total_cleared} cache keys for model: {model_name}")
    return total_cleared

def clear_view_cache(view_name):
    """Clear cache for a specific view"""
    pattern = f"views.decorators.cache.cache_*{view_name}*"
    return clear_cache_pattern(pattern)

# Specific cache clearing functions for your models
def clear_category_cache():
    """Clear all category-related cache"""
    return clear_model_cache("Category")

def clear_product_cache():
    """Clear all product-related cache"""
    return clear_model_cache("Product")
