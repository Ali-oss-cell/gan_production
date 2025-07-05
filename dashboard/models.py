from django.db import models
from django.conf import settings
from users.models import BaseUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

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

class SharedMediaPost(models.Model):
    """
    Model for dashboard admins to share media from search results to gallery.
    Uses GenericForeignKey to reference any type of media (TalentMedia, BandMedia, Item images, etc.)
    """
    # Who shared it (must be dashboard user or admin)
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_media_posts'
    )
    
    # What was shared (flexible to handle different media types)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    shared_content = GenericForeignKey('content_type', 'object_id')
    
    # Admin's caption/commentary
    caption = models.TextField(blank=True, help_text="Admin's commentary about the shared media")
    
    # Metadata
    shared_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Optional: categorization for gallery organization
    CATEGORY_CHOICES = [
        ('featured', 'Featured Work'),
        ('inspiration', 'Inspiration'),
        ('trending', 'Trending'),
        ('spotlight', 'Artist Spotlight'),
        ('general', 'General'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    
    class Meta:
        ordering = ['-shared_at']
        unique_together = ['content_type', 'object_id']  # Prevent duplicate shares of same media by any admin
        
    def __str__(self):
        return f"Shared by {self.shared_by.email} at {self.shared_at}"
    
    def get_original_owner(self):
        """Get the original owner of the shared content"""
        content = self.shared_content
        
        if hasattr(content, 'talent'):
            # TalentMedia
            return content.talent.user
        elif hasattr(content, 'band'):
            # BandMedia
            return content.band.creator.user
        elif hasattr(content, 'BackGroundJobsProfile'):
            # Item models (Prop, Costume, etc.)
            return content.BackGroundJobsProfile.user
        
        return None
    
    def get_content_info(self):
        """Get basic info about the shared content"""
        content = self.shared_content
        
        if hasattr(content, 'media_file'):
            # TalentMedia or BandMedia
            return {
                'type': 'media',
                'name': getattr(content, 'name', 'Untitled'),
                'media_type': getattr(content, 'media_type', 'unknown'),
                'file_url': content.media_file.url if content.media_file else None,
                'thumbnail_url': getattr(content, 'thumbnail', {}).url if hasattr(content, 'thumbnail') and content.thumbnail else None,
            }
        elif hasattr(content, 'image'):
            # Item models
            return {
                'type': 'item',
                'name': getattr(content, 'name', 'Untitled'),
                'item_type': content.__class__.__name__.lower(),
                'file_url': content.image.url if content.image else None,
                'price': getattr(content, 'price', None),
            }
            
        return {'type': 'unknown', 'name': 'Unknown Content'}
    
    def get_attribution_text(self):
        """Get text for attribution to original creator"""
        owner = self.get_original_owner()
        if owner:
            return f"Originally by {owner.first_name} {owner.last_name} (@{owner.email})"
        return "Original creator unknown"

@receiver([post_save, post_delete], sender=SharedMediaPost)
def clear_sharing_status_cache(sender, instance, **kwargs):
    """
    Clear sharing status cache when SharedMediaPost is created, updated, or deleted.
    This ensures the frontend gets consistent sharing status information.
    """
    try:
        from .utils import clear_sharing_status_cache
        clear_sharing_status_cache(
            content_type=instance.content_type,
            object_id=instance.object_id
        )
    except Exception as e:
        # Log error but don't fail the operation
        print(f"Error clearing sharing status cache: {e}")
