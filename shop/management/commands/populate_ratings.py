from django.core.management.base import BaseCommand
from shop.models import Rating

class Command(BaseCommand):
    help = 'Populate product ratings'

    def handle(self, *args, **options):
        for i in range(1, 6):
            Rating.objects.get_or_create(value=i)

        self.stdout.write(self.style.SUCCESS('Product ratings populated successfully.'))