from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Listing


class Command(BaseCommand):
    help = 'Test the 10% markup functionality for car listings'

    def handle(self, *args, **options):
        # Create a test listing
        test_listing = Listing.objects.create(
            make="Maruti",
            model="Swift",
            year=2020,
            km=25000,
            fuel="Petrol",
            trans="Manual",
            price=500000,  # Original predicted price
            original_predicted_price=500000,
            location="Mumbai",
            status="pending"
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created test listing: {test_listing}')
        )
        self.stdout.write(f'Original price: ₹{test_listing.original_predicted_price:,}')
        self.stdout.write(f'Current price: ₹{test_listing.price:,}')
        self.stdout.write(f'Status: {test_listing.status}')
        
        # Simulate approval (you would normally do this through admin)
        test_listing.status = "approved"
        if test_listing.original_predicted_price:
            markup_price = int(test_listing.original_predicted_price * 1.10)
            test_listing.price = markup_price
        
        test_listing.approved_at = timezone.now()
        test_listing.save()
        
        self.stdout.write(
            self.style.SUCCESS('\nAfter approval with 10% markup:')
        )
        self.stdout.write(f'Original price: ₹{test_listing.original_predicted_price:,}')
        self.stdout.write(f'Final price: ₹{test_listing.price:,}')
        self.stdout.write(f'Markup amount: ₹{test_listing.get_markup_amount():,}')
        self.stdout.write(f'Markup percentage: {test_listing.get_markup_percentage()}%')
        self.stdout.write(f'Status: {test_listing.status}')
        
        # Clean up
        test_listing.delete()
        self.stdout.write(
            self.style.SUCCESS('\nTest completed successfully! Test listing deleted.')
        )