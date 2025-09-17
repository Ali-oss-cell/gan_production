from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import BaseUser
import secrets

class Command(BaseCommand):
    help = 'Test email verification for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user to test verification')
        parser.add_argument(
            '--reset-token',
            action='store_true',
            help='Generate a new verification token for the user',
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = BaseUser.objects.get(email=email)
        except BaseUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} does not exist')
            )
            return

        self.stdout.write(f'User: {user.email}')
        self.stdout.write(f'Email Verified: {user.email_verified}')
        self.stdout.write(f'Current Token: {user.email_verification_token}')
        self.stdout.write(f'Token Created: {user.email_verification_token_created}')
        
        if options['reset_token']:
            # Generate new token
            user.email_verification_token = secrets.token_urlsafe(32)
            user.email_verification_token_created = timezone.now()
            user.email_verified = False
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'New token generated: {user.email_verification_token}')
            )
            
            # Show verification URL
            verification_url = f"http://localhost:8000/api/verify-email/?token={user.email_verification_token}"
            self.stdout.write(f'Verification URL: {verification_url}')
            
        if user.email_verification_token:
            # Check token age
            if user.email_verification_token_created:
                token_age = timezone.now() - user.email_verification_token_created
                is_expired = token_age.total_seconds() > (24 * 3600)  # 24 hours
                self.stdout.write(f'Token Age: {token_age}')
                self.stdout.write(f'Token Expired: {is_expired}')
                
            # Show test URL
            verification_url = f"http://localhost:8000/api/verify-email/?token={user.email_verification_token}"
            self.stdout.write(f'Test this URL: {verification_url}')
        else:
            self.stdout.write('No verification token available')
