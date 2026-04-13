from django.core.management.base import BaseCommand
from core.models import Listing, SparePart

class Command(BaseCommand):
    help = 'Check listing and spare parts statuses'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('  DATABASE STATUS CHECK'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        # Check Listings
        self.stdout.write(self.style.WARNING('📋 CAR LISTINGS:'))
        self.stdout.write('-' * 60)
        
        try:
            listings = Listing.objects.all()
            total = listings.count()
            self.stdout.write(f"Total listings in database: {total}")
            
            if total == 0:
                self.stdout.write(self.style.ERROR('  ❌ No listings found!'))
                self.stdout.write('  💡 Create listings at: http://localhost:8000/sell-car/')
            else:
                # Check status distribution
                try:
                    from django.db.models import Count
                    status_counts = Listing.objects.values('status').annotate(count=Count('status'))
                    self.stdout.write('\nStatus breakdown:')
                    for item in status_counts:
                        status = item['status']
                        count = item['count']
                        if status == 'approved':
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Approved: {count}'))
                        elif status == 'pending':
                            self.stdout.write(self.style.WARNING(f'  ⏳ Pending: {count}'))
                        elif status == 'rejected':
                            self.stdout.write(self.style.ERROR(f'  ❌ Rejected: {count}'))
                        else:
                            self.stdout.write(f'  ❓ {status}: {count}')
                except Exception:
                    pass
                
                # Show recent listings
                self.stdout.write('\nRecent listings:')
                for listing in listings.order_by('-created_at')[:5]:
                    try:
                        status = getattr(listing, 'status', 'NO_STATUS')
                        status_icon = '✅' if status == 'approved' else '⏳' if status == 'pending' else '❌'
                        self.stdout.write(f'  {status_icon} ID {listing.id}: {listing.make} {listing.model} {listing.year} - {status}')
                    except Exception as e:
                        self.stdout.write(f'  ❓ ID {listing.id}: {listing.make} {listing.model} - Error: {e}')
                
                # Check if any are approved
                approved_count = Listing.objects.filter(status='approved').count()
                if approved_count == 0:
                    self.stdout.write(self.style.ERROR('\n  ⚠️  WARNING: No approved listings!'))
                    self.stdout.write('  💡 Listings won\'t show in shop until approved.')
                    self.stdout.write('  💡 Run: python manage.py approve_all_listings')
                else:
                    self.stdout.write(self.style.SUCCESS(f'\n  ✅ {approved_count} listing(s) will show in shop'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error checking listings: {e}'))
        
        # Check Spare Parts
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.WARNING('🔧 SPARE PARTS:'))
        self.stdout.write('-' * 60)
        
        try:
            spare_parts = SparePart.objects.all()
            total = spare_parts.count()
            active = SparePart.objects.filter(is_active=True).count()
            
            self.stdout.write(f'Total spare parts: {total}')
            self.stdout.write(f'Active spare parts: {active}')
            
            if total == 0:
                self.stdout.write(self.style.ERROR('  ❌ No spare parts found!'))
                self.stdout.write('  💡 Run: python manage.py add_sample_spareparts')
            elif active == 0:
                self.stdout.write(self.style.ERROR('  ⚠️  WARNING: No active spare parts!'))
                self.stdout.write('  💡 Activate spare parts in admin panel')
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✅ {active} spare part(s) will show in shop'))
                
                # Show sample spare parts
                self.stdout.write('\nSample spare parts:')
                for part in spare_parts.filter(is_active=True)[:5]:
                    self.stdout.write(f'  ✅ {part.sku}: {part.name} - ₹{part.price}')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error checking spare parts: {e}'))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write('='*60)
        
        try:
            listings_ok = Listing.objects.filter(status='approved').count() > 0
            spareparts_ok = SparePart.objects.filter(is_active=True).count() > 0
            
            if listings_ok and spareparts_ok:
                self.stdout.write(self.style.SUCCESS('✅ Everything looks good!'))
                self.stdout.write('   Visit: http://localhost:8000/shop/')
                self.stdout.write('   Visit: http://localhost:8000/spare-parts/')
            else:
                if not listings_ok:
                    self.stdout.write(self.style.WARNING('⚠️  Shop will be empty (no approved listings)'))
                    self.stdout.write('   Fix: python manage.py approve_all_listings')
                if not spareparts_ok:
                    self.stdout.write(self.style.WARNING('⚠️  Spare parts will be empty'))
                    self.stdout.write('   Fix: python manage.py add_sample_spareparts')
        except Exception:
            pass
        
        self.stdout.write('='*60 + '\n')