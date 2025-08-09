from django.core.management.base import BaseCommand
from shop.models import Category


class Command(BaseCommand):
    help = 'Populate categories'

    def handle(self, *args, **options):
        categories = [
            'watch',
            'electronics',
            't-shirts',
            'footwear',
            'sharies',
            'pants',
            'baby\'s dresses',
            'home & garden',
            'sports',
            'toys',
            'books',
            'health & beauty',
            'pet supplies',
            'automotive',
        ]

        for category in categories:
            Category.objects.get_or_create(name=category)

        self.stdout.write(self.style.SUCCESS('Categories populated successfully.'))