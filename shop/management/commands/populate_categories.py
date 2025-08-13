from shop import models
import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Populate categories from extracted JSON data"
 
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before importing'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes'
        )

    def handle(self, *args, **kwargs):
        clear_existing = kwargs['clear']
        dry_run = kwargs['dry_run']
        
        # Get the correct path to the JSON file
        json_file = os.path.join(settings.BASE_DIR.parent, 'assistant_programm', 'categories_simple.json')
        
        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f"Error: File not found - {json_file}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Loading category data from: {json_file}"))

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading JSON: {e}"))
            return

        # Get the categories list from the JSON structure
        categories_list = data.get('categories', [])
        
        if not categories_list:
            self.stdout.write(self.style.ERROR("No categories found in the JSON file"))
            return

        self.stdout.write(f"Found {len(categories_list)} categories to process")

        if dry_run:
            self._dry_run_analysis(categories_list)
            return

        if clear_existing:
            self.stdout.write(self.style.WARNING('Clearing existing categories...'))
            models.Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing categories cleared'))

        # Import categories
        created_count = 0
        updated_count = 0
        
        for category in categories_list:
            try:
                name = category.get('name', '')
                display_name = category.get('display_name', name.replace('-', ' ').title())
                
                category_obj, created = models.Category.objects.update_or_create(
                    name=display_name,
                    defaults={
                        'slug': slugify(display_name),
                        'description': category.get('description', ''),
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"✓ Created: {display_name}")
                else:
                    updated_count += 1
                    self.stdout.write(f"↻ Updated: {display_name}")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing category {category.get('name', 'unknown')}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"\nCategories import completed!"
            f"\n- Created: {created_count} categories"
            f"\n- Updated: {updated_count} categories"
        ))

    def _dry_run_analysis(self, categories_list):
        """Show what would be imported without making changes"""
        self.stdout.write(self.style.WARNING('\n=== DRY RUN ANALYSIS ==='))
        
        existing_categories = set(models.Category.objects.values_list('name', flat=True))
        
        new_categories = []
        existing_updates = []
        
        for category in categories_list:
            display_name = category.get('display_name', category.get('name', '').replace('-', ' ').title())
            
            if display_name in existing_categories:
                existing_updates.append(display_name)
            else:
                new_categories.append(display_name)
        
        self.stdout.write(f'\nTotal categories to process: {len(categories_list)}')
        
        if new_categories:
            self.stdout.write(f'\nNew categories to create ({len(new_categories)}):')
            for cat in new_categories:
                self.stdout.write(f'  + {cat}')
        
        if existing_updates:
            self.stdout.write(f'\nExisting categories to update ({len(existing_updates)}):')
            for cat in existing_updates:
                self.stdout.write(f'  ↻ {cat}')
        
        self.stdout.write(f'\n=== READY TO IMPORT ===')
        self.stdout.write(f'Run without --dry-run to import these categories')