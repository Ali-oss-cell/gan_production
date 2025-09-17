from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import BaseUser
from users.serializers import send_verification_code_email
import random

class Command(BaseCommand):
    help = 'Test email verification for a specific user (code-based)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user to test verification')
        parser.add_argument(
            '--reset-code',
            action='store_true',
            help='Generate a new verification code for the user',
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send verification code email to the user',
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
        self.stdout.write(f'Current Code: {user.email_verification_code}')
        self.stdout.write(f'Code Created: {user.email_verification_code_created}')
        
        if options['reset_code']:
            # Generate new code
            verification_code = str(random.randint(100000, 999999))
            user.email_verification_code = verification_code
            user.email_verification_code_created = timezone.now()
            user.email_verified = False
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'New code generated: {user.email_verification_code}')
            )
            
        if options['send_email'] and user.email_verification_code:
            # Send verification code email
            success = send_verification_code_email(user.email, user.email_verification_code)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'Verification code email sent to {user.email}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send email to {user.email}')
                )
            
        if user.email_verification_code:
            # Check code age
            if user.email_verification_code_created:
                code_age = timezone.now() - user.email_verification_code_created
                is_expired = code_age.total_seconds() > (24 * 3600)  # 24 hours
                self.stdout.write(f'Code Age: {code_age}')
                self.stdout.write(f'Code Expired: {is_expired}')
                
            # Show test instructions
            self.stdout.write('To test verification:')
            self.stdout.write('POST /api/verify-code/')
            self.stdout.write(f'{{"email": "{user.email}", "code": "{user.email_verification_code}"}}')
        else:
            self.stdout.write('No verification code available')
