import os
from django.core.management.base import BaseCommand
from shop.models import Slider


class Command(BaseCommand):
    help = 'Create image slider with all images in ImageSlider directory'

    def handle(self, *args, **options):
        # Clear existing sliders
        Slider.objects.all().delete()
        
        # Directory containing slider images
        image_dir = 'media/ImageSlider/'
        
        if not os.path.exists(image_dir):
            self.stdout.write(self.style.ERROR(f'Directory {image_dir} does not exist'))
            return
        
        # Get all image files
        image_files = [f for f in os.listdir(image_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        if not image_files:
            self.stdout.write(self.style.WARNING('No image files found'))
            return
        
        # Create slider entries
        for image_file in image_files:
            # Use relative path for the image field (ImageSlider/filename)
            image_path = f'ImageSlider/{image_file}'
            slider = Slider.objects.create(
                image=image_path,
                title=f'Slider {image_file.split(".")[0]}'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created slider: {slider.title}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(image_files)} sliders')
        )