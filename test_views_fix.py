#!/usr/bin/env python
"""
Simple test script to verify the view fixes work correctly.
This script tests that the views handle AnonymousUser objects correctly.
"""
import os
import sys
import django
from django.conf import settings

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'root.settings')

# Setup Django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from shop.views import CartListView, RemoveFromCartView, OrderViewSet, UserOrderList
from shop.models import Cart, Order

def test_anonymous_user_handling():
    """Test that views handle AnonymousUser correctly."""
    factory = RequestFactory()
    request = factory.get('/')
    request.user = AnonymousUser()
    
    print("Testing CartListView with AnonymousUser...")
    try:
        view = CartListView()
        view.request = request
        queryset = view.get_queryset()
        print(f"✓ CartListView.get_queryset() returned: {queryset}")
        print(f"✓ CartListView.get_queryset() count: {queryset.count()}")
    except Exception as e:
        print(f"✗ CartListView failed: {e}")
        return False
    
    print("\nTesting RemoveFromCartView with AnonymousUser...")
    try:
        view = RemoveFromCartView()
        view.request = request
        queryset = view.get_queryset()
        print(f"✓ RemoveFromCartView.get_queryset() returned: {queryset}")
        print(f"✓ RemoveFromCartView.get_queryset() count: {queryset.count()}")
    except Exception as e:
        print(f"✗ RemoveFromCartView failed: {e}")
        return False
    
    print("\nTesting OrderViewSet with AnonymousUser...")
    try:
        view = OrderViewSet()
        view.request = request
        queryset = view.get_queryset()
        print(f"✓ OrderViewSet.get_queryset() returned: {queryset}")
        print(f"✓ OrderViewSet.get_queryset() count: {queryset.count()}")
    except Exception as e:
        print(f"✗ OrderViewSet failed: {e}")
        return False
    
    print("\nTesting UserOrderList with AnonymousUser...")
    try:
        view = UserOrderList()
        view.request = request
        queryset = view.get_queryset()
        print(f"✓ UserOrderList.get_queryset() returned: {queryset}")
        print(f"✓ UserOrderList.get_queryset() count: {queryset.count()}")
    except Exception as e:
        print(f"✗ UserOrderList failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing views with AnonymousUser to verify fixes...")
    print("=" * 50)
    
    success = test_anonymous_user_handling()
    
    print("=" * 50)
    if success:
        print("✅ All tests passed! The fix should resolve the TypeError.")
    else:
        print("❌ Some tests failed. There may be additional issues to fix.")
