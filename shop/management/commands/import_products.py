"""
Management command to import products from products.json.

Reads every product from the JSON file, downloads all images
(thumbnail + gallery) into the media directory, and creates
the corresponding Django model records:
  Category, Rating, ItemType, Item, ItemImage


Written With AI model - Claude.
"""

import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from shop.models import Category, Item, ItemImage, ItemType, Rating


class Command(BaseCommand):
    help = "Import products from products.json and download their images"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="products.json",
            help="Path to the JSON file (default: products.json in project root)",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip products whose product_id (SKU) already exists",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _slugify(text: str) -> str:
        """Turn an arbitrary string into a filesystem-safe slug."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        return re.sub(r"[\s-]+", "-", text)

    def _download_image(self, url: str, upload_to: str, filename: str) -> str | None:
        """
        Download *url* and save it under  MEDIA_ROOT / upload_to / filename.
        Returns the relative media path (e.g. 'images/some-file.webp')
        or None on failure.
        """
        dest_dir = os.path.join(settings.MEDIA_ROOT, upload_to)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, filename)

        # Skip if the file already exists on disk
        if os.path.exists(dest_path):
            self.stdout.write(f"  ⏭  Already exists: {dest_path}")
            return os.path.join(upload_to, filename)

        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=30, stream=True)
                resp.raise_for_status()
                with open(dest_path, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=8192):
                        fh.write(chunk)
                self.stdout.write(f"  ✅ Downloaded: {filename}")
                return os.path.join(upload_to, filename)
            except requests.RequestException as exc:
                self.stderr.write(
                    self.style.WARNING(
                        f"  ⚠  Attempt {attempt + 1}/3 failed for {url}: {exc}"
                    )
                )
                time.sleep(2)

        self.stderr.write(self.style.ERROR(f"  ❌ Failed to download: {url}"))
        return None

    @staticmethod
    def _ext_from_url(url: str) -> str:
        """Extract the file extension from a URL (e.g. '.webp')."""
        parsed = urlparse(url)
        return os.path.splitext(parsed.path)[1] or ".webp"

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        json_path = options["file"]
        skip_existing = options["skip_existing"]

        # Resolve relative path against project root (BASE_DIR)
        if not os.path.isabs(json_path):
            json_path = os.path.join(settings.BASE_DIR, json_path)

        if not os.path.exists(json_path):
            raise CommandError(f"JSON file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        products = data.get("products", [])
        if not products:
            raise CommandError("No products found in JSON file")

        self.stdout.write(
            self.style.SUCCESS(f"\n📦 Found {len(products)} products to import\n")
        )

        created_count = 0
        skipped_count = 0
        error_count = 0

        for idx, p in enumerate(products, start=1):
            sku = p.get("sku", f"UNKNOWN-{idx}")
            title = p.get("title", "Untitled")

            self.stdout.write(
                self.style.HTTP_INFO(
                    f"\n[{idx}/{len(products)}] Processing: {title} ({sku})"
                )
            )

            # Check for existing product
            if skip_existing and Item.objects.filter(product_id=sku).exists():
                self.stdout.write(f"  ⏭  Skipped (already exists)")
                skipped_count += 1
                continue

            try:
                self._import_single_product(p, sku, title)
                created_count += 1
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"  ❌ Error importing {sku}: {exc}")
                )
                error_count += 1

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(f"✅ Created : {created_count}")
        )
        if skipped_count:
            self.stdout.write(f"⏭  Skipped : {skipped_count}")
        if error_count:
            self.stdout.write(
                self.style.ERROR(f"❌ Errors  : {error_count}")
            )
        self.stdout.write("=" * 60 + "\n")

    def _import_single_product(self, p: dict, sku: str, title: str):
        """Create one Item (+ related records) from a product dict."""

        # ---- Category ---------------------------------------------------
        cat_name = (p.get("category") or "Uncategorized").title()
        category, _ = Category.objects.get_or_create(name=cat_name)

        # ---- ItemType (from first tag) ----------------------------------
        tags = p.get("tags", [])
        type_name = tags[0].title() if tags else cat_name
        item_type, _ = ItemType.objects.get_or_create(name=type_name)

        # ---- Rating (rounded to int, clamped 1-5) -----------------------
        raw_rating = p.get("rating", 0)
        rating_val = max(1, min(5, round(raw_rating)))
        rating_obj, _ = Rating.objects.get_or_create(value=rating_val)

        # ---- Price / discount -------------------------------------------
        price = int(round(p.get("price", 0)))
        discount_pct = p.get("discountPercentage", 0)
        discount_price = int(round(price * (1 - discount_pct / 100)))

        # ---- Description (truncate to model max_length) -----------------
        description = (p.get("description") or "")[:260]

        # ---- Stock ------------------------------------------------------
        stock = p.get("stock", 0)

        # ---- Brand ------------------------------------------------------
        brand = p.get("brand", "Unknown")

        # ---- Download thumbnail -----------------------------------------
        slug = self._slugify(title)
        thumb_url = p.get("thumbnail", "")
        thumb_path = None
        if thumb_url:
            ext = self._ext_from_url(thumb_url)
            thumb_filename = f"{slug}-thumb{ext}"
            thumb_path = self._download_image(thumb_url, "images", thumb_filename)

        # ---- Create or update the Item ----------------------------------
        item, item_created = Item.objects.update_or_create(
            product_id=sku,
            defaults={
                "title": title[:200],
                "price": price,
                "discount_price": discount_price,
                "number_of_items": stock,
                "brand_name": brand[:100],
                "category": category,
                "type": item_type,
                "ratings": rating_obj,
                "description": description,
                "is_featured": False,
                "is_bestselling": False,
            },
        )

        # Assign the thumbnail image path directly
        if thumb_path:
            item.image = thumb_path
            item.save(update_fields=["image"])

        action = "Created" if item_created else "Updated"
        self.stdout.write(f"  📝 {action}: {item}")

        # ---- Download gallery images & create ItemImage records ---------
        image_urls = p.get("images", [])
        for img_idx, img_url in enumerate(image_urls, start=1):
            ext = self._ext_from_url(img_url)
            img_filename = f"{slug}-{img_idx}{ext}"
            img_path = self._download_image(img_url, "item_images", img_filename)
            if img_path:
                # Avoid duplicate ItemImage rows
                if not ItemImage.objects.filter(item=item, image=img_path).exists():
                    ItemImage.objects.create(item=item, image=img_path)
                    self.stdout.write(f"  🖼  Added gallery image {img_idx}")
