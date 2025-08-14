#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'root.settings')
django.setup()

from shop.models import Slider

def populate_sliders():
    """Create sample slider records if none exist"""
    existing_count = Slider.objects.count()
    print(f"Existing slider records: {existing_count}")
    
    if existing_count == 0:
        # Sample slider data
        slider_data = [
            {"title": "Summer Sale", "image": "ImageSlider/6021260.jpg"},
            {"title": "New Arrivals", "image": "ImageSlider/6031488.jpg"},
            {"title": "Special Offers", "image": "ImageSlider/786598.jpg"},
            {"title": "Best Deals", "image": "ImageSlider/7865986.jpg"},
            {"title": "Featured Products", "image": "ImageSlider/7919477.jpg"},
        ]
        
        for data in slider_data:
            slider = Slider.objects.create(
                title=data["title"],
                image=data["image"]
            )
            print(f"Created slider: {slider.title} - {slider.image}")
        
        print(f"Created {len(slider_data)} slider records")
    else:
        print("Slider records already exist:")
        for slider in Slider.objects.all():
            print(f"- {slider.title}: {slider.image}")

if __name__ == "__main__":
    populate_sliders()
