import random
from django.core.management.base import BaseCommand
from shop.models import Product, TopSellingProducts

class Command(BaseCommand):
    help = 'Create 25 random TopSellingProducts'

    def handle(self, *args, **kwargs):
        TopSellingProducts.objects.all().delete()  # clear existing
        products = list(Product.objects.all())

        if not products:
            self.stdout.write(self.style.ERROR('No products found.'))
            return

        for product in random.sample(products, min(25, len(products))):
            TopSellingProducts.objects.create(product=product)
            self.stdout.write(f"Added: {product.title}")

        self.stdout.write(self.style.SUCCESS(f"Total TopSellingProducts: {TopSellingProducts.objects.count()}"))
