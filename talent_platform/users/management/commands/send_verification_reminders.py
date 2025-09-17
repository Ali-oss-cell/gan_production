from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from datetime import timedelta
from users.models import BaseUser
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send email verification reminders to unverified users every 24 hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get users who need verification reminders
        now = timezone.now()
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        # Find unverified users who either:
        # 1. Never had a verification email sent, OR
        # 2. Had their last verification email sent more than 24 hours ago
        unverified_users = BaseUser.objects.filter(
            email_verified=False,
            is_active=True
        ).filter(
            models.Q(last_verification_email_sent__isnull=True) |
            models.Q(last_verification_email_sent__lt=twenty_four_hours_ago)
        )
        
        count = unverified_users.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No users need verification reminders at this time.'))
            return
        
        self.stdout.write(f'Found {count} users who need verification reminders...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No emails will be sent'))
            for user in unverified_users:
                self.stdout.write(f'  - Would send reminder to: {user.email}')
            return
        
        # Send verification reminders
        sent_count = 0
        failed_count = 0
        
        for user in unverified_users:
            try:
                # Generate new verification token if needed
                if not user.email_verification_token:
                    self._generate_verification_token(user)
                
                # Send verification email
                success = self._send_verification_reminder(user)
                
                if success:
                    # Update last verification email sent timestamp
                    user.last_verification_email_sent = now
                    user.save(update_fields=['last_verification_email_sent'])
                    sent_count += 1
                    self.stdout.write(f'  ✓ Sent reminder to: {user.email}')
                else:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to send to: {user.email}'))
                    
            except Exception as e:
                failed_count += 1
                logger.error(f'Error sending verification reminder to {user.email}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'  ✗ Error sending to {user.email}: {str(e)}'))
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Verification reminders sent: {sent_count}')
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to send: {failed_count}'))
        self.stdout.write('='*50)

    def _generate_verification_token(self, user):
        """Generate a new verification token for the user"""
        import secrets
        from django.utils import timezone
        
        user.email_verification_token = secrets.token_urlsafe(32)
        user.email_verification_token_created = timezone.now()
        user.save(update_fields=['email_verification_token', 'email_verification_token_created'])

    def _send_verification_reminder(self, user):
        """Send verification reminder email"""
        try:
            import os
            from django.core.mail import send_mail
            from django.conf import settings
            
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            verification_url = f"{frontend_url}/verify-email?token={user.email_verification_token}"
            
            subject = 'Reminder: Please verify your email address'
            message = f"""
Hi {user.first_name},

This is a friendly reminder to verify your email address for your account.

Please click the link below to verify your email:
{verification_url}

If you didn't create this account, you can safely ignore this email.

Best regards,
The Talent Platform Team
            """.strip()
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            logger.error(f'Failed to send verification reminder to {user.email}: {str(e)}')
            return False
