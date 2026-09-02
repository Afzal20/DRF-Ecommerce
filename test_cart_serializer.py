import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
django.setup()

from shop.models import Cart  # noqa: E402
from shop.serializers import CartSerilizers  # noqa: E402

carts = Cart.objects.all()
serializer = CartSerilizers(carts, many=True)
print(serializer.data[0] if serializer.data else "No cart items")
