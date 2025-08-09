"""
Django management command to import products with local images from dummy_products_local_images.json
Usage: python manage.py import_products_with_images
"""

import json
import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from django.utils.dateparse import parse_datetime
from shop.models import Product, ProductImage, ProductReview
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import products with local images from JSON file'

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

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        dry_run = options['dry_run']
        limit = options['limit']

        # Get the full path to the JSON file
        base_dir = settings.BASE_DIR.parent  # Go up one level from Backend/
        json_file_path = os.path.join(base_dir, file_path)

        if not os.path.exists(json_file_path):
            self.stdout.write(
                self.style.ERROR(f'JSON file not found: {json_file_path}')
            )
            return

        self.stdout.write(f'Loading data from: {json_file_path}')

        # Load JSON data
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading JSON file: {str(e)}')
            )
            return

        products_data = data.get('products', [])
        
        if limit:
            products_data = products_data[:limit]
            self.stdout.write(f'Limiting import to {limit} products')

        self.stdout.write(f'Found {len(products_data)} products to import')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self._dry_run_analysis(products_data)
            return

        # Clear existing products if requested
        if clear_existing:
            self.stdout.write('Clearing existing products...')
            Product.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing products cleared'))

        # Import products
        created_count = 0
        updated_count = 0
        error_count = 0

        for product_data in products_data:
            try:
                created, updated = self._import_product(product_data)
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

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\nImport completed!'
            f'\n- Created: {created_count} products'
            f'\n- Updated: {updated_count} products'
            f'\n- Errors: {error_count} products'
        ))

    def _dry_run_analysis(self, products_data):
        """Analyze what would be imported without making changes"""
        media_root = settings.MEDIA_ROOT
        found_images = 0
        missing_images = 0
        
        for product_data in products_data[:5]:  # Check first 5 products
            product_id = product_data.get('id')
            self.stdout.write(f'\nProduct ID {product_id}: {product_data.get("title", "No title")}')
            
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

            # Check product images
            images = product_data.get('images', [])
            self.stdout.write(f'  Product images: {len(images)}')
            for i, image_path in enumerate(images):
                full_image_path = os.path.join(media_root, image_path)
                if os.path.exists(full_image_path):
                    self.stdout.write(f'    ✓ Image {i+1}: {image_path}')
                    found_images += 1
                else:
                    self.stdout.write(f'    ✗ Missing image {i+1}: {image_path}')
                    missing_images += 1

            # Check QR code
            qr_code_path = product_data.get('meta', {}).get('qrCode')
            if qr_code_path:
                full_qr_path = os.path.join(media_root, qr_code_path)
                if os.path.exists(full_qr_path):
                    self.stdout.write(f'  ✓ QR Code: {qr_code_path}')
                    found_images += 1
                else:
                    self.stdout.write(f'  ✗ Missing QR code: {qr_code_path}')
                    missing_images += 1

        self.stdout.write(f'\nImage Analysis Summary:')
        self.stdout.write(f'  Found images: {found_images}')
        self.stdout.write(f'  Missing images: {missing_images}')

    def _import_product(self, product_data):
        """Import a single product with its images"""
        product_id = product_data.get('id')
        
        # Parse datetime fields
        created_at = self._parse_datetime(product_data.get('meta', {}).get('createdAt'))
        updated_at = self._parse_datetime(product_data.get('meta', {}).get('updatedAt'))

        # Get or create product
        product, created = Product.objects.get_or_create(
            id=product_id,
            defaults={
                'title': product_data.get('title', ''),
                'description': product_data.get('description', ''),
                'category': product_data.get('category', ''),
                'price': product_data.get('price', 0),
                'discount_percentage': product_data.get('discountPercentage', 0),
                'rating': product_data.get('rating', 0),
                'stock': product_data.get('stock', 0),
                'tags': product_data.get('tags', []),
                'brand': product_data.get('brand', ''),
                'sku': product_data.get('sku', ''),
                'weight': product_data.get('weight', 0),
                'width': product_data.get('dimensions', {}).get('width', 0),
                'height': product_data.get('dimensions', {}).get('height', 0),
                'depth': product_data.get('dimensions', {}).get('depth', 0),
                'warranty_information': product_data.get('warrantyInformation', ''),
                'shipping_information': product_data.get('shippingInformation', ''),
                'availability_status': product_data.get('availabilityStatus', ''),
                'return_policy': product_data.get('returnPolicy', ''),
                'minimum_order_quantity': product_data.get('minimumOrderQuantity', 1),
                'created_at': created_at or datetime.now(),
                'updated_at': updated_at or datetime.now(),
                'barcode': product_data.get('meta', {}).get('barcode', ''),
            }
        )

        if not created:
            # Update existing product
            for field, value in {
                'title': product_data.get('title'),
                'description': product_data.get('description'),
                'category': product_data.get('category'),
                'price': product_data.get('price'),
                'discount_percentage': product_data.get('discountPercentage'),
                'rating': product_data.get('rating'),
                'stock': product_data.get('stock'),
                'tags': product_data.get('tags'),
                'brand': product_data.get('brand'),
                'weight': product_data.get('weight'),
                'width': product_data.get('dimensions', {}).get('width'),
                'height': product_data.get('dimensions', {}).get('height'),
                'depth': product_data.get('dimensions', {}).get('depth'),
                'warranty_information': product_data.get('warrantyInformation'),
                'shipping_information': product_data.get('shippingInformation'),
                'availability_status': product_data.get('availabilityStatus'),
                'return_policy': product_data.get('returnPolicy'),
                'minimum_order_quantity': product_data.get('minimumOrderQuantity'),
                'updated_at': updated_at or datetime.now(),
                'barcode': product_data.get('meta', {}).get('barcode'),
            }.items():
                if value is not None:
                    setattr(product, field, value)
            product.save()

        # Handle thumbnail
        self._handle_image_field(product, 'thumbnail', product_data.get('thumbnail'))

        # Handle QR code
        qr_code_path = product_data.get('meta', {}).get('qrCode')
        self._handle_image_field(product, 'qr_code', qr_code_path)

        # Handle product images
        images = product_data.get('images', [])
        if created or not product.images.exists():
            # Clear existing images for updates
            if not created:
                product.images.all().delete()
            
            for order, image_path in enumerate(images):
                if self._create_product_image(product, image_path, order):
                    self.stdout.write(f'    Added image {order + 1} for product {product_id}')

        # Handle reviews
        reviews = product_data.get('reviews', [])
        if created or not product.reviews.exists():
            if not created:
                product.reviews.all().delete()
            
            for review_data in reviews:
                self._create_product_review(product, review_data)

        return created, not created

    def _handle_image_field(self, product, field_name, image_path):
        """Handle saving an image to a model field"""
        if not image_path:
            return

        media_root = settings.MEDIA_ROOT
        full_image_path = os.path.join(media_root, image_path)
        
        if os.path.exists(full_image_path):
            try:
                with open(full_image_path, 'rb') as f:
                    file_content = File(f)
                    filename = os.path.basename(image_path)
                    getattr(product, field_name).save(filename, file_content, save=True)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to save {field_name} for product {product.id}: {str(e)}')
                )

    def _create_product_image(self, product, image_path, order):
        """Create a ProductImage instance"""
        if not image_path:
            return False

        media_root = settings.MEDIA_ROOT
        full_image_path = os.path.join(media_root, image_path)
        
        if os.path.exists(full_image_path):
            try:
                product_image = ProductImage.objects.create(
                    product=product,
                    image_order=order
                )
                
                with open(full_image_path, 'rb') as f:
                    file_content = File(f)
                    filename = os.path.basename(image_path)
                    product_image.image.save(filename, file_content, save=True)
                
                return True
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to create product image: {str(e)}')
                )
        
        return False

    def _create_product_review(self, product, review_data):
        """Create a ProductReview instance"""
        review_date = self._parse_datetime(review_data.get('date'))
        
        ProductReview.objects.create(
            product=product,
            rating=review_data.get('rating', 0),
            comment=review_data.get('comment', ''),
            date=review_date or datetime.now(),
            reviewer_name=review_data.get('reviewerName', ''),
            reviewer_email=review_data.get('reviewerEmail', ''),
        )

    def _parse_datetime(self, date_string):
        """Parse datetime string safely"""
        if not date_string:
            return None
        
        try:
            return parse_datetime(date_string)
        except (ValueError, TypeError):
            return None
