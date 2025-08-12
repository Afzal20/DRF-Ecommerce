from django.core.management.base import BaseCommand
from shop.models import Districts

class Command(BaseCommand):
    help = 'Populate the database with districts of Bangladesh'

    def handle(self, *args, **kwargs):
        districts = [
            "Barguna", "Barishal", "Bhola", "Jhalokathi", "Patuakhali", "Pirojpur",
            "Bandarban", "Brahmanbaria", "Chandpur", "Chattogram", "Cumilla", "Cox's Bazar",
            "Feni", "Khagrachari", "Lakshmipur", "Noakhali", "Rangamati", "Dhaka", "Faridpur",
            "Gazipur", "Gopalganj", "Kishoreganj", "Madaripur", "Manikganj", "Munshiganj",
            "Narayanganj", "Narsingdi", "Rajbari", "Shariatpur", "Tangail", "Bagerhat",
            "Chuadanga", "Jashore", "Jhenaidah", "Khulna", "Kushtia", "Magura", "Meherpur",
            "Narail", "Satkhira", "Jamalpur", "Mymensingh", "Netrokona", "Sherpur", "Bogura",
            "Joypurhat", "Naogaon", "Natore", "Chapai Nawabganj", "Pabna", "Rajshahi",
            "Sirajgonj", "Dinajpur", "Gaibandha", "Kurigram", "Lalmonirhat", "Nilphamari",
            "Panchagarh", "Rangpur", "Thakurgaon", "Habiganj", "Moulvibazar", "Sunamganj",
            "Sylhet"
        ]

        for district in districts:
            Districts.objects.get_or_create(title=district)

        self.stdout.write(self.style.SUCCESS('Successfully populated districts.'))