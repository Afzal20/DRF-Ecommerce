import requests
from django.core.management.base import BaseCommand
from shop.models import Product, ProductImage, ProductReview
from datetime import datetime

class Command(BaseCommand):
    help = "Import products from DummyJSON API"

    def handle(self, *args, **kwargs):
        base_url = "https://dummyjson.com/products"
        limit = 100   # max allowed per request
        skip = 0
        total_imported = 0

        while True:
            url = f"{base_url}?limit={limit}&skip={skip}"
            response = requests.get(url)
            data = response.json()

            products = data.get("products", [])
            if not products:
                break

            for p in products:
                product_obj, created = Product.objects.update_or_create(
                    sku=p.get("sku", f"SKU-{p['id']}"),
                    defaults={
                        "title": p["title"],
                        "description": p["description"],
                        "category": p["category"],
                        "price": p["price"],
                        "discount_percentage": p.get("discountPercentage", 0),
                        "rating": p.get("rating", 0),
                        "stock": p.get("stock", 0),
                        "tags": p.get("tags", []),
                        "brand": p.get("brand", ""),
                        "weight": p.get("weight", 0),
                        "width": p["dimensions"]["width"],
                        "height": p["dimensions"]["height"],
                        "depth": p["dimensions"]["depth"],
                        "warranty_information": p.get("warrantyInformation", ""),
                        "shipping_information": p.get("shippingInformation", ""),
                        "availability_status": p.get("availabilityStatus", ""),
                        "return_policy": p.get("returnPolicy", ""),
                        "minimum_order_quantity": p.get("minimumOrderQuantity", 1),
                        "created_at": datetime.fromisoformat(p["meta"]["createdAt"].replace("Z", "+00:00")),
                        "updated_at": datetime.fromisoformat(p["meta"]["updatedAt"].replace("Z", "+00:00")),
                        "barcode": p["meta"]["barcode"],
                        "qr_code": p["meta"]["qrCode"],
                        "thumbnail": p.get("thumbnail", ""),
                    }
                )

                # Images
                for img_url in p.get("images", []):
                    ProductImage.objects.get_or_create(product=product_obj, image_url=img_url)

                # Reviews
                for r in p.get("reviews", []):
                    ProductReview.objects.get_or_create(
                        product=product_obj,
                        rating=r["rating"],
                        comment=r["comment"],
                        date=datetime.fromisoformat(r["date"].replace("Z", "+00:00")),
                        reviewer_name=r["reviewerName"],
                        reviewer_email=r["reviewerEmail"]
                    )

                total_imported += 1

            skip += limit

        self.stdout.write(self.style.SUCCESS(f"Imported {total_imported} products successfully!"))
