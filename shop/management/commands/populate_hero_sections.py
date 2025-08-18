from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from shop.models import HeroSection
import os
import io
import base64
from datetime import datetime

# A tiny 1x1 PNG (transparent) to avoid external dependencies like Pillow
TINY_PNG_BASE64 = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)

DEFAULT_TITLES = [
    "Experience Pure Sound - Your Perfect Headphones Awaits!",
    "Next-Level Gaming Starts Here - Discover PlayStation 5 Today!",
    "Power Meets Elegance - Apple MacBook Pro is Here for you!",
    "Immersive Sound, Unmatched Comfort - Meet Your Next Headphones",
    "Upgrade Your Game - PlayStation Deals You Can’t Miss",
    "Create Without Limits - MacBook Pro for Pros",
    "Feel the Beat - Premium Headphones, Best Prices",
    "Game On - Explore the Latest PS5 Accessories",
    "Work Faster, Create Better - MacBook Pro Offers",
    "Top Tech Picks - Handpicked Deals for You",
]

DEFAULT_OFFERS = [
    "Limited Time Offer 30% Off",
    "Hurry up only few lefts!",
    "Exclusive Deal 40% Off",
    "New Season, New Deals",
    "Weekend Flash Sale",
    "Save More with Bundles",
    "Mega Discount Week",
    "Student Specials Available",
    "Free Shipping on Orders Over $50",
    "Today Only: Extra 10% Off",
]

BTN1_TEXT = [
    "Buy now", "Shop Now", "Order Now", "Grab Deal", "Get Yours",
    "Buy Today", "Add to Cart", "Shop Offers", "Start Now", "Claim Deal",
]

BTN2_TEXT = [
    "Find more", "Explore Deals", "Learn More", "See Details", "Discover",
    "Browse More", "View All", "See Collection", "Explore Now", "Read More",
]

BTN1_URLS = [
    "https://example.com/buy",
    "https://example.com/shop",
    "https://example.com/order",
    "https://example.com/deal",
    "https://example.com/get",
    "https://example.com/buy-today",
    "https://example.com/cart",
    "https://example.com/offers",
    "https://example.com/start",
    "https://example.com/claim",
]

BTN2_URLS = [
    "https://example.com/more",
    "https://example.com/explore",
    "https://example.com/learn",
    "https://example.com/details",
    "https://example.com/discover",
    "https://example.com/browse",
    "https://example.com/all",
    "https://example.com/collection",
    "https://example.com/explore-now",
    "https://example.com/read",
]

class Command(BaseCommand):
    help = "Seed HeroSection with N sample slides (default 10). Creates tiny PNGs under MEDIA_ROOT/HeroSection if missing."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=10, help="Number of slides to create (default 10)")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing HeroSection records before creating new ones",
        )

    def handle(self, *args, **options):
        count = options["count"]
        do_reset = options["reset"]

        if do_reset:
            deleted = HeroSection.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted existing HeroSection records: {deleted}"))

        created = 0

        # Ensure media/HeroSection directory exists
        media_root = getattr(settings, "MEDIA_ROOT", None)
        if not media_root:
            self.stderr.write(self.style.ERROR("MEDIA_ROOT is not configured. Aborting."))
            return

        hero_dir = os.path.join(media_root, "HeroSection")
        os.makedirs(hero_dir, exist_ok=True)

        for i in range(count):
            title = DEFAULT_TITLES[i % len(DEFAULT_TITLES)]
            offer = DEFAULT_OFFERS[i % len(DEFAULT_OFFERS)]
            b1_text = BTN1_TEXT[i % len(BTN1_TEXT)]
            b2_text = BTN2_TEXT[i % len(BTN2_TEXT)]
            b1_url = BTN1_URLS[i % len(BTN1_URLS)]
            b2_url = BTN2_URLS[i % len(BTN2_URLS)]

            # Create a tiny PNG file bytes for each slide (unique name)
            filename = f"hero_{i+1}.png"
            image_rel_path = os.path.join("HeroSection", filename).replace("\\", "/")

            # If file doesn't exist, write it
            full_path = os.path.join(hero_dir, filename)
            if not os.path.exists(full_path):
                try:
                    with open(full_path, "wb") as f:
                        f.write(base64.b64decode(TINY_PNG_BASE64))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Failed to write image {full_path}: {e}"))

            # Create record only if a duplicate with same title doesn't exist
            obj, was_created = HeroSection.objects.get_or_create(
                title=title,
                defaults={
                    "offer": offer,
                    "button_1_Text": b1_text,
                    "button_1_navigate_url": b1_url,
                    "button_2_Text": b2_text,
                    "button_2_navigate_url": b2_url,
                    # Assign relative path; Django will serve from MEDIA_URL
                    "image": image_rel_path,
                },
            )

            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created HeroSection: {obj.title}"))
            else:
                # Update missing fields if needed (optional)
                updated = False
                if not obj.offer:
                    obj.offer = offer; updated = True
                if not obj.button_1_Text:
                    obj.button_1_Text = b1_text; updated = True
                if not obj.button_1_navigate_url:
                    obj.button_1_navigate_url = b1_url; updated = True
                if not obj.button_2_Text:
                    obj.button_2_Text = b2_text; updated = True
                if not obj.button_2_navigate_url:
                    obj.button_2_navigate_url = b2_url; updated = True
                if not obj.image:
                    obj.image = image_rel_path; updated = True
                if updated:
                    obj.save()
                    self.stdout.write(self.style.NOTICE(f"Updated existing HeroSection: {obj.title}"))
                else:
                    self.stdout.write(f"Skipped existing HeroSection: {obj.title}")

        self.stdout.write(self.style.SUCCESS(f"Seeding complete. Created {created} HeroSection record(s)."))
