import json
import os
import random

import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
django.setup()


def run():
    from django.contrib.auth import get_user_model

    from shop.models import Category, Item, ItemImage, ItemType, Rating, Vendor

    User = get_user_model()

    json_path = "/home/dev-dir/Ecommerce/DRF-Ecommerce/prepared_products.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    if not items:
        items = data.get("products", [])

    print(f"Loaded {len(items)} items from {json_path}")

    # Create dummy vendors
    vendor_names = [
        "Tech Hub",
        "Fashion Store",
        "General Goods",
        "Electro World",
        "Home Essentials",
    ]
    vendors = []
    for i, v_name in enumerate(vendor_names):
        user, _ = User.objects.get_or_create(
            email=f"vendor{i}@example.com", defaults={"is_active": True}
        )
        if not user.has_usable_password():
            user.set_password("vendor123")
            user.save()
        vendor, _ = Vendor.objects.get_or_create(
            user=user,
            defaults={
                "store_name": v_name,
                "store_description": f"Welcome to {v_name}!",
            },
        )
        vendors.append(vendor)

    created_count = 0
    updated_count = 0
    error_count = 0

    for item_data in items:
        sku = item_data.get("product_id") or item_data.get("sku")
        title = item_data.get("title", "Untitled")

        try:
            # 1. Get or Create Category
            cat_name = item_data.get("category", "Uncategorized").title()
            category, _ = Category.objects.get_or_create(name=cat_name)

            # 2. Get or Create ItemType
            type_name = item_data.get("type")
            if not type_name:
                tags = item_data.get("tags", [])
                type_name = tags[0].title() if tags else cat_name
            else:
                type_name = type_name.title()

            item_type, _ = ItemType.objects.get_or_create(name=type_name)

            # 3. Get or Create Rating
            rating_val = int(item_data.get("ratings", 3))
            rating_obj, _ = Rating.objects.get_or_create(value=rating_val)

            # 4. Item Fields
            assigned_vendor = random.choice(vendors)

            defaults = {
                "title": title[:200],
                "price": int(item_data.get("price", 0)),
                "discount_price": int(item_data.get("discount_price", 0)),
                "number_of_items": int(item_data.get("number_of_items", 0)),
                "brand_name": item_data.get("brand_name", "Unknown")[:100],
                "category": category,
                "type": item_type,
                "ratings": rating_obj,
                "vendor": assigned_vendor,
                "description": item_data.get("description", "")[:260],
                "is_featured": item_data.get("is_featured", False),
                "is_bestselling": item_data.get("is_bestselling", False),
            }

            # Thumbnail
            image_path = item_data.get("image") or item_data.get("thumbnail")
            if image_path:
                defaults["image"] = image_path

            item, created = Item.objects.update_or_create(
                product_id=sku, defaults=defaults
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            # 5. Gallery Images
            image_urls = item_data.get("images", [])
            if not image_urls and "original_image_urls" in item_data:
                image_urls = item_data["original_image_urls"]

            for img_path in image_urls:
                if not ItemImage.objects.filter(item=item, image=img_path).exists():
                    ItemImage.objects.create(item=item, image=img_path)

        except Exception as e:
            print(f"Error importing {sku}: {e}")
            error_count += 1

    print("=" * 60)
    print(f"Created: {created_count}")
    print(f"Updated: {updated_count}")
    print(f"Errors: {error_count}")
    print("=" * 60)


if __name__ == "__main__":
    run()
