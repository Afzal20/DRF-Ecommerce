import random
from django.core.management.base import BaseCommand
from shop.models import Category, TopCategory

class Command(BaseCommand):
    help = 'Create 10 random TopCategories'

    def handle(self, *args, **kwargs):
        TopCategory.objects.all().delete()  # clear existing
        
        # Filter categories that have images and are active
        categories_with_images = list(Category.objects.filter(
            image__isnull=False,  # Must have an image
            is_active=True  # Must be active
        ).exclude(image=''))  # Exclude empty image paths

        if not categories_with_images:
            self.stdout.write(self.style.ERROR('No categories with images found.'))
            return

        # Create up to 10 top categories, or less if we don't have enough categories
        count = min(10, len(categories_with_images))
        selected_categories = random.sample(categories_with_images, count)
        
        for category in selected_categories:
            TopCategory.objects.create(category=category)
            self.stdout.write(f"Added: {category.name} (Image: {category.image.name if category.image else 'None'})")

        self.stdout.write(self.style.SUCCESS(f"Total TopCategories with images: {TopCategory.objects.count()}"))
