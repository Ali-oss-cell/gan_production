from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import BulkEmail, EmailRecipient
import logging

logger = logging.getLogger(__name__)

class DashboardEmailService:
    """Service for sending bulk emails to talent users from dashboard"""
    
    @staticmethod
    def create_bulk_email(sender, subject, message, search_criteria=None):
        """Create a new bulk email record"""
        return BulkEmail.objects.create(
            sender=sender,
            subject=subject,
            message=message,
            search_criteria=search_criteria or {}
        )
    
    @staticmethod
    def add_recipients(bulk_email, user_ids):
        """Add recipients to bulk email"""
        from users.models import BaseUser
        
        recipients = []
        for user_id in user_ids:
            try:
                user = BaseUser.objects.get(id=user_id)
                recipient, created = EmailRecipient.objects.get_or_create(
                    bulk_email=bulk_email,
                    user=user
                )
                if created:
                    recipients.append(recipient)
            except BaseUser.DoesNotExist:
                logger.warning(f"User {user_id} not found for bulk email {bulk_email.id}")
        
        # Update total recipients count
        bulk_email.total_recipients = bulk_email.recipients.count()
        bulk_email.save()
        
        return recipients
    
    @staticmethod
    def send_bulk_email(bulk_email_id):
        """Send bulk email to all recipients"""
        try:
            bulk_email = BulkEmail.objects.get(id=bulk_email_id)
            bulk_email.status = 'sending'
            bulk_email.save()
            
            # Get pending recipients
            pending_recipients = bulk_email.recipients.filter(status='pending')
            
            emails_sent = 0
            emails_failed = 0
            
            for recipient in pending_recipients:
                try:
                    # Prepare email content
                    context = {
                        'recipient': recipient.user,
                        'message': bulk_email.message,
                        'sender': bulk_email.sender,
                    }
                    
                    # Send email
                    success = send_mail(
                        subject=bulk_email.subject,
                        message=bulk_email.message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient.user.email],
                        fail_silently=False,
                    )
                    
                    if success:
                        recipient.status = 'sent'
                        recipient.sent_at = timezone.now()
                        emails_sent += 1
                    else:
                        recipient.status = 'failed'
                        recipient.error_message = 'Email sending failed'
                        emails_failed += 1
                    
                    recipient.save()
                    
                except Exception as e:
                    recipient.status = 'failed'
                    recipient.error_message = str(e)
                    recipient.save()
                    emails_failed += 1
                    logger.error(f"Failed to send email to {recipient.user.email}: {e}")
            
            # Update bulk email status
            bulk_email.emails_sent = emails_sent
            bulk_email.emails_failed = emails_failed
            bulk_email.status = 'sent' if emails_failed == 0 else 'failed'
            bulk_email.sent_at = timezone.now()
            bulk_email.save()
            
            return {
                'success': True,
                'emails_sent': emails_sent,
                'emails_failed': emails_failed,
                'total_recipients': bulk_email.total_recipients
            }
            
        except BulkEmail.DoesNotExist:
            logger.error(f"BulkEmail {bulk_email_id} not found")
            return {'success': False, 'error': 'Bulk email not found'}
        except Exception as e:
            logger.error(f"Error sending bulk email {bulk_email_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_email_statistics(bulk_email_id):
        """Get statistics for a bulk email campaign"""
        try:
            bulk_email = BulkEmail.objects.get(id=bulk_email_id)
            
            return {
                'total_recipients': bulk_email.total_recipients,
                'emails_sent': bulk_email.emails_sent,
                'emails_failed': bulk_email.emails_failed,
                'status': bulk_email.status,
                'sent_at': bulk_email.sent_at,
                'created_at': bulk_email.created_at,
            }
        except BulkEmail.DoesNotExist:
            return None 