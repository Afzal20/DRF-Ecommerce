import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
django.setup()

from shop.serializers import CartSerilizers  # noqa: E402

data = {"item": 1, "quantity": 1, "item_color_code": "", "item_size": ""}
serializer = CartSerilizers(data=data)
if not serializer.is_valid():
    print(serializer.errors)
else:
    print("Valid!")
