from django.core.management.base import BaseCommand
from core.models import Listing

class Command(BaseCommand):
    help = 'Approve all pending listings for development'

    def handle(self, *args, **options):
        try:
            # Update all listings to approved status
            updated = Listing.objects.exclude(status='approved').update(status='approved')
            self.stdout.write(
                self.style.SUCCESS(f'Successfully approved {updated} listings')
            )
            
            # Show current status
            total = Listing.objects.count()
            approved = Listing.objects.filter(status='approved').count()
            self.stdout.write(f'Total listings: {total}')
            self.stdout.write(f'Approved listings: {approved}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )