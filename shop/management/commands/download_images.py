"""
Django Management Command for downloading and storing product images locally
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import sys
import json
from pathlib import Path

# Add the assistant_programm directory to Python path to import our downloader
current_dir = Path(__file__).parent.parent.parent.parent.parent
assistant_dir = current_dir / "assistant_programm"
sys.path.insert(0, str(assistant_dir))

try:
    from download_images import ImageDownloadManager
except ImportError:
    ImageDownloadManager = None


class Command(BaseCommand):
    help = 'Download and store product images locally from URLs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input-file',
            type=str,
            default='dummy_products.json',
            help='Path to the JSON file containing products with image URLs'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=5,
            help='Number of concurrent download threads (default: 5)'
        )
        parser.add_argument(
            '--media-path',
            type=str,
            help='Custom media path for storing images (defaults to MEDIA_ROOT/downloaded_images)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be downloaded without actually downloading'
        )

    def handle(self, *args, **options):
        if ImageDownloadManager is None:
            raise CommandError("ImageDownloadManager not found. Make sure download_images.py is in assistant_programm/")

        input_file = options['input_file']
        workers = options['workers']
        media_path = options['media_path']
        dry_run = options['dry_run']

        # Resolve input file path
        if not os.path.isabs(input_file):
            # Look for the file in assistant_programm directory
            assistant_path = current_dir / "assistant_programm" / input_file
            if assistant_path.exists():
                input_file = str(assistant_path)
            else:
                raise CommandError(f"Input file not found: {input_file}")

        # Set default media path if not provided
        if not media_path:
            media_path = os.path.join(settings.MEDIA_ROOT, 'downloaded_images')

        self.stdout.write(f"Input file: {input_file}")
        self.stdout.write(f"Media path: {media_path}")
        self.stdout.write(f"Workers: {workers}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No files will be downloaded"))
            
            # Just analyze the file
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                products = data.get('products', [])
                self.stdout.write(f"Found {len(products)} products")
                
                total_images = 0
                for product in products:
                    images = product.get('images', [])
                    thumbnail = product.get('thumbnail')
                    qr_code = product.get('meta', {}).get('qrCode')
                    
                    count = len(images)
                    if thumbnail:
                        count += 1
                    if qr_code:
                        count += 1
                    
                    total_images += count
                    
                    if count > 0:
                        self.stdout.write(f"Product {product.get('id')}: {count} images to download")
                
                self.stdout.write(f"Total images to download: {total_images}")
                return
                
            except Exception as e:
                raise CommandError(f"Error analyzing input file: {e}")

        # Initialize the download manager
        try:
            manager = ImageDownloadManager(media_path)
        except Exception as e:
            raise CommandError(f"Failed to initialize ImageDownloadManager: {e}")

        # Start downloading
        self.stdout.write("Starting image download process...")
        
        try:
            output_file = manager.download_all_images(input_file, workers)
            
            if output_file:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Image download completed!")
                )
                self.stdout.write(f"📁 Updated products file: {output_file}")
                self.stdout.write(f"🖼️  Images stored in: {manager.base_media_path}")
                self.stdout.write(f"✅ Downloaded: {len(manager.download_log)} images")
                
                if manager.failed_downloads:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  {len(manager.failed_downloads)} images failed to download")
                    )
                    self.stdout.write("Check image_download.log for details")
                    
                # Show some statistics
                self.stdout.write("\n📊 Download Statistics:")
                self.stdout.write(f"   - Total attempted: {len(manager.download_log) + len(manager.failed_downloads)}")
                self.stdout.write(f"   - Successful: {len(manager.download_log)}")
                self.stdout.write(f"   - Failed: {len(manager.failed_downloads)}")
                
                if len(manager.download_log) > 0:
                    success_rate = (len(manager.download_log) / (len(manager.download_log) + len(manager.failed_downloads))) * 100
                    self.stdout.write(f"   - Success rate: {success_rate:.1f}%")
                
            else:
                raise CommandError("Image download failed")
                
        except Exception as e:
            raise CommandError(f"Error during download process: {e}")
