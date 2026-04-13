"""
Management command to check Google OAuth configuration
Usage: python manage.py check_oauth
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Check Google OAuth configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Google OAuth Configuration Check ===\n'))
        
        # Check Client ID
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
        if client_id:
            self.stdout.write(self.style.SUCCESS(f'✓ Client ID: {client_id[:20]}...'))
        else:
            self.stdout.write(self.style.ERROR('✗ Client ID: NOT CONFIGURED'))
        
        # Check Client Secret
        client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET") or getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", "")
        if client_secret:
            self.stdout.write(self.style.SUCCESS(f'✓ Client Secret: {client_secret[:10]}... (hidden)'))
        else:
            self.stdout.write(self.style.ERROR('✗ Client Secret: NOT CONFIGURED'))
        
        # Check Redirect URI
        redirect_uri = os.environ.get("GOOGLE_OAUTH_REDIRECT_URI") or getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "")
        if redirect_uri:
            self.stdout.write(self.style.SUCCESS(f'✓ Redirect URI: {redirect_uri}'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Redirect URI: Using default'))
        
        # Overall status
        self.stdout.write('\n')
        if client_id and client_secret:
            self.stdout.write(self.style.SUCCESS('✓ Google OAuth is CONFIGURED and ready to use!'))
            self.stdout.write('\nTest it at: http://localhost:8000/oauth-test/')
        else:
            self.stdout.write(self.style.ERROR('✗ Google OAuth is NOT CONFIGURED'))
            self.stdout.write('\nPlease follow the setup guide in GOOGLE_OAUTH_SETUP.md')
            self.stdout.write('\nQuick start: See OAUTH_QUICKSTART.md')
        
        self.stdout.write('\n')
