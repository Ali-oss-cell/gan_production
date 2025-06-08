from django.db import models
from django.conf import settings
from users.models import BaseUser

class BulkEmail(models.Model):
    """Model for tracking bulk email campaigns sent to talent"""
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_bulk_emails'
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Search criteria used to select recipients
    search_criteria = models.JSONField(null=True, blank=True)
    
    # Email status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    
    # Email statistics
    total_recipients = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    emails_failed = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bulk Email'
        verbose_name_plural = 'Bulk Emails'
    
    def __str__(self):
        return f"{self.subject} - {self.sender.email} ({self.status})"

class EmailRecipient(models.Model):
    """Model for tracking individual email recipients within a bulk email"""
    
    bulk_email = models.ForeignKey(
        BulkEmail,
        on_delete=models.CASCADE,
        related_name='recipients'
    )
    user = models.ForeignKey(
        BaseUser,
        on_delete=models.CASCADE,
        related_name='received_emails'
    )
    
    # Email delivery status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('bulk_email', 'user')
        ordering = ['-created_at']
        verbose_name = 'Email Recipient'
        verbose_name_plural = 'Email Recipients'
    
    def __str__(self):
        return f"{self.user.email} - {self.bulk_email.subject} ({self.status})"
