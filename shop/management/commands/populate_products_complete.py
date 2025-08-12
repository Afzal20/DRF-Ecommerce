import json
import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from django.utils.dateparse import parse_datetime
from shop.models import Product, ProductImage, ProductReview
from datetime import datetime
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populate products with complete data and local images from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='assistant_programm/dummy_products_local_images.json',
            help='Path to the JSON file with local image paths (relative to project root)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products before importing'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of products to import (for testing)'
        )
        parser.add_argument(
            '--start-from',
            type=int,
            default=0,
            help='Start importing from specific product index'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        dry_run = options['dry_run']
        limit = options['limit']
        start_from = options['start_from']

        # Get the full path to the JSON file
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR.parent, file_path)

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(f'Loading data from: {file_path}')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON file: {e}'))
            return

        products_data = data.get('products', [])
        
        if not products_data:
            self.stdout.write(self.style.ERROR('No products found in the JSON file'))
            return

        # Apply start_from and limit
        if start_from > 0:
            products_data = products_data[start_from:]
            self.stdout.write(f'Starting from product index {start_from}')

        if limit:
            products_data = products_data[:limit]
            self.stdout.write(f'Limited to {limit} products')

        self.stdout.write(f'Found {len(products_data)} products to process')

        if dry_run:
            self._dry_run_analysis(products_data)
            return

        if clear_existing:
            self.stdout.write(self.style.WARNING('Clearing existing products...'))
            Product.objects.all().delete()
            ProductImage.objects.all().delete()
            ProductReview.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing products cleared'))

        # Import products
        self._import_products(products_data)

    def _import_products(self, products_data):
        """Import products with transactions for data integrity"""
        created_count = 0
        updated_count = 0
        error_count = 0
        
        media_root = settings.MEDIA_ROOT

        for product_data in products_data:
            try:
                with transaction.atomic():
                    product, created, updated = self._create_or_update_product(product_data, media_root)
                    
                    if created:
                        created_count += 1
                    elif updated:
                        updated_count += 1
                    
                    if (created_count + updated_count) % 10 == 0:
                        self.stdout.write(f'Processed {created_count + updated_count} products...')
                        
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error importing product ID {product_data.get("id", "unknown")}: {str(e)}')
                )
                logger.error(f'Error importing product {product_data.get("id")}: {str(e)}')

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\nImport completed!'
            f'\n- Created: {created_count} products'
            f'\n- Updated: {updated_count} products'
            f'\n- Errors: {error_count} products'
        ))

    def _create_or_update_product(self, product_data, media_root):
        """Create or update a single product with all related data"""
        product_id = product_data.get('id')
        
        # Parse meta data
        meta = product_data.get('meta', {})
        created_at = parse_datetime(meta.get('createdAt')) or datetime.now()
        updated_at = parse_datetime(meta.get('updatedAt')) or datetime.now()

        # Parse dimensions
        dimensions = product_data.get('dimensions', {})

        # Create or update product
        product, created = Product.objects.update_or_create(
            id=product_id,
            defaults={
                'title': product_data.get('title', ''),
                'description': product_data.get('description', ''),
                'category': product_data.get('category', ''),
                'price': float(product_data.get('price', 0)),
                'discount_percentage': float(product_data.get('discountPercentage', 0)),
                'rating': float(product_data.get('rating', 0)),
                'stock': int(product_data.get('stock', 0)),
                'tags': product_data.get('tags', []),
                'brand': product_data.get('brand', ''),
                'sku': product_data.get('sku', ''),
                'weight': float(product_data.get('weight', 0)),
                'width': float(dimensions.get('width', 0)),
                'height': float(dimensions.get('height', 0)),
                'depth': float(dimensions.get('depth', 0)),
                'warranty_information': product_data.get('warrantyInformation', ''),
                'shipping_information': product_data.get('shippingInformation', ''),
                'availability_status': product_data.get('availabilityStatus', ''),
                'return_policy': product_data.get('returnPolicy', ''),
                'minimum_order_quantity': int(product_data.get('minimumOrderQuantity', 1)),
                'created_at': created_at,
                'updated_at': updated_at,
                'barcode': meta.get('barcode', ''),
            }
        )

        # Handle thumbnail
        thumbnail_path = product_data.get('thumbnail')
        if thumbnail_path:
            self._handle_image_file(product, 'thumbnail', thumbnail_path, media_root)

        # Handle QR code
        qr_code_path = meta.get('qrCode')
        if qr_code_path:
            self._handle_image_file(product, 'qr_code', qr_code_path, media_root)

        # Handle product images
        if created or not product.images.exists():
            self._handle_product_images(product, product_data.get('images', []), media_root)

        # Handle reviews
        if created or not product.reviews.exists():
            self._handle_product_reviews(product, product_data.get('reviews', []))

        return product, created, not created

    def _handle_image_file(self, product, field_name, relative_path, media_root):
        if not relative_path:
            return

        full_path = os.path.join(media_root, relative_path)
        
        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as f:
                    file_name = os.path.basename(relative_path)
                    django_file = File(f, name=file_name)
                    setattr(product, field_name, django_file)
                    product.save(update_fields=[field_name])
            except Exception as e:
                logger.warning(f'Failed to set {field_name} for product {product.id}: {str(e)}')
        else:
            logger.warning(f'Image file not found: {full_path}')

    def _handle_product_images(self, product, image_paths, media_root):
        # Clear existing images if any
        product.images.all().delete()

        for order, image_path in enumerate(image_paths):
            if not image_path:
                continue

            full_path = os.path.join(media_root, image_path)
            
            if os.path.exists(full_path):
                try:
                    product_image = ProductImage.objects.create(
                        product=product,
                        image_order=order
                    )
                    
                    with open(full_path, 'rb') as f:
                        file_name = os.path.basename(image_path)
                        django_file = File(f, name=file_name)
                        product_image.image = django_file
                        product_image.save()
                        
                except Exception as e:
                    logger.warning(f'Failed to create product image {order} for product {product.id}: {str(e)}')
            else:
                logger.warning(f'Product image file not found: {full_path}')

    def _handle_product_reviews(self, product, reviews_data):
        # Clear existing reviews if any
        product.reviews.all().delete()

        for review_data in reviews_data:
            try:
                review_date = parse_datetime(review_data.get('date')) or datetime.now()
                
                ProductReview.objects.create(
                    product=product,
                    rating=int(review_data.get('rating', 5)),
                    comment=review_data.get('comment', ''),
                    date=review_date,
                    reviewer_name=review_data.get('reviewerName', ''),
                    reviewer_email=review_data.get('reviewerEmail', '')
                )
            except Exception as e:
                logger.warning(f'Failed to create review for product {product.id}: {str(e)}')

    def _dry_run_analysis(self, products_data):
        media_root = settings.MEDIA_ROOT
        found_images = 0
        missing_images = 0
        
        self.stdout.write(self.style.WARNING('\n=== DRY RUN ANALYSIS ==='))
        
        for i, product_data in enumerate(products_data[:5]):  # Check first 5 products
            product_id = product_data.get('id')
            self.stdout.write(f'\nProduct {i+1} - ID {product_id}: {product_data.get("title", "No title")}')
            
            # Check thumbnail
            thumbnail_path = product_data.get('thumbnail')
            if thumbnail_path:
                full_thumbnail_path = os.path.join(media_root, thumbnail_path)
                if os.path.exists(full_thumbnail_path):
                    self.stdout.write(f'  ✓ Thumbnail: {thumbnail_path}')
                    found_images += 1
                else:
                    self.stdout.write(f'  ✗ Missing thumbnail: {thumbnail_path}')
                    missing_images += 1

            # Check QR code
            meta = product_data.get('meta', {})
            qr_code_path = meta.get('qrCode')
            if qr_code_path:
                full_qr_path = os.path.join(media_root, qr_code_path)
                if os.path.exists(full_qr_path):
                    self.stdout.write(f'  ✓ QR Code: {qr_code_path}')
                    found_images += 1
                else:
                    self.stdout.write(f'  ✗ Missing QR code: {qr_code_path}')
                    missing_images += 1

            # Check product images
            images = product_data.get('images', [])
            self.stdout.write(f'  Product images: {len(images)}')
            for j, image_path in enumerate(images):
                full_image_path = os.path.join(media_root, image_path)
                if os.path.exists(full_image_path):
                    self.stdout.write(f'    ✓ Image {j+1}: {image_path}')
                    found_images += 1
                else:
                    self.stdout.write(f'    ✗ Missing image {j+1}: {image_path}')
                    missing_images += 1

            # Check reviews
            reviews = product_data.get('reviews', [])
            self.stdout.write(f'  Reviews: {len(reviews)}')

        self.stdout.write(f'\n=== SUMMARY ===')
        self.stdout.write(f'Total products to process: {len(products_data)}')
        self.stdout.write(f'Sample check - Found images: {found_images}')
        self.stdout.write(f'Sample check - Missing images: {missing_images}')
        
        if missing_images == 0:
            self.stdout.write(self.style.SUCCESS('✓ All sample images are available!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ {missing_images} sample images are missing'))
