from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access/edit it.
    Assumes the model instance has an `user` or `user_name` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Allow admin users full access
        if request.user and request.user.is_staff:
            return True

        # Check if the object has a 'user' attribute
        if hasattr(obj, "user"):
            return obj.user == request.user

        # Check if the object has a 'user_name' attribute (used in Cart model)
        if hasattr(obj, "user_name"):
            return obj.user_name == request.user

        # Check if the object is tied to an order which has a user (e.g. OrderItem, Refund)
        if hasattr(obj, "order") and hasattr(obj.order, "user"):
            return obj.order.user == request.user

        return False
