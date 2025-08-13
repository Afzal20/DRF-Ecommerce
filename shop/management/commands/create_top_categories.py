import random
from django.core.management.base import BaseCommand
from shop.models import Category, TopCategory

class Command(BaseCommand):
    help = 'Create 10 random TopCategories'

    def handle(self, *args, **kwargs):
        TopCategory.objects.all().delete()  # clear existing
        categories = list(Category.objects.all())

        if not categories:
            self.stdout.write(self.style.ERROR('No categories found.'))
            return

        # Create up to 10 top categories, or less if we don't have enough categories
        count = min(10, len(categories))
        for category in random.sample(categories, count):
            TopCategory.objects.create(category=category)
            self.stdout.write(f"Added: {category.name}")

        self.stdout.write(self.style.SUCCESS(f"Total TopCategories: {TopCategory.objects.count()}"))
