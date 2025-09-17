from celery import shared_task
from django.utils import timezone
from django.db import models
from datetime import timedelta
from users.models import BaseUser
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_verification_reminders():
    """
    Celery task to send email verification reminders to unverified users
    This should be called every 24 hours via a cron job or scheduler
    """
    try:
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
        logger.info(f'Found {count} users who need verification reminders')
        
        if count == 0:
            return {'status': 'success', 'message': 'No users need verification reminders', 'count': 0}
        
        # Send verification reminders
        sent_count = 0
        failed_count = 0
        
        for user in unverified_users:
            try:
                # Generate new verification token if needed
                if not user.email_verification_token:
                    _generate_verification_token(user)
                
                # Send verification email
                success = _send_verification_reminder(user)
                
                if success:
                    # Update last verification email sent timestamp
                    user.last_verification_email_sent = now
                    user.save(update_fields=['last_verification_email_sent'])
                    sent_count += 1
                    logger.info(f'Sent verification reminder to: {user.email}')
                else:
                    failed_count += 1
                    logger.error(f'Failed to send verification reminder to: {user.email}')
                    
            except Exception as e:
                failed_count += 1
                logger.error(f'Error sending verification reminder to {user.email}: {str(e)}')
        
        result = {
            'status': 'success',
            'message': f'Verification reminders sent: {sent_count}, Failed: {failed_count}',
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_processed': count
        }
        
        logger.info(f'Verification reminder task completed: {result}')
        return result
        
    except Exception as e:
        error_msg = f'Error in send_verification_reminders task: {str(e)}'
        logger.error(error_msg)
        return {'status': 'error', 'message': error_msg}

def _generate_verification_token(user):
    """Generate a new verification token for the user"""
    import secrets
    from django.utils import timezone
    
    user.email_verification_token = secrets.token_urlsafe(32)
    user.email_verification_token_created = timezone.now()
    user.save(update_fields=['email_verification_token', 'email_verification_token_created'])

def _send_verification_reminder(user):
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
