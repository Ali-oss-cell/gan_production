from django.db import models
from django.conf import settings
from django.forms import ValidationError
# Create your models here.
from users .models import BaseUser
import os
import uuid
from .utils.media_processor import MediaProcessor
from django.core.files.base import ContentFile
import tempfile
import subprocess

class TalentUserProfile(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='talent_user')
    is_verified = models.BooleanField(default=False)
    profile_complete = models.BooleanField(default=False)  # Track profile completion status
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    aboutyou = models.TextField(blank=True, null=True)

    ACCOUNT_TYPES = [
        ('platinum', 'Platinum'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('free', 'Free'),
    ]
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='free')
    
    def has_specialization(self):
        """
        Check if the user has at least one specialization (VisualWorker, ExpressiveWorker, or HybridWorker).
        """
        has_visual = hasattr(self, 'visual_worker')
        has_expressive = hasattr(self, 'expressive_worker')
        has_hybrid = hasattr(self, 'hybrid_worker')
        return has_visual or has_expressive or has_hybrid
    
    def update_profile_completion(self):
        """
        Update the profile_complete status based on whether the user has at least one specialization.
        """
        self.profile_complete = self.has_specialization()
        self.save(update_fields=['profile_complete'])
        
    def get_profile_score(self):
        score_breakdown = {
            'total': 0,
            'account_tier': 0,
            'verification': 0,
            'profile_completion': 0,
            'media_content': 0,
            'specialization': 0,
            'details': {}
        }
        # Account tier (unchanged)
        if self.account_type == 'platinum':
            score_breakdown['account_tier'] = 50
            score_breakdown['details']['account_tier'] = 'Platinum account: +50 points'
        elif self.account_type == 'gold':
            score_breakdown['account_tier'] = 40
            score_breakdown['details']['account_tier'] = 'Gold account: +40 points'
        elif self.account_type == 'silver':
            score_breakdown['account_tier'] = 30
            score_breakdown['details']['account_tier'] = 'Silver account: +30 points'
        else:
            score_breakdown['account_tier'] = 10
            score_breakdown['details']['account_tier'] = 'Free account: +10 points'
        # Verification (unchanged)
        if self.is_verified:
            score_breakdown['verification'] = 20
            score_breakdown['details']['verification'] = 'Verified profile: +20 points'
        else:
            score_breakdown['details']['verification'] = 'Not verified: +0 points (get verified for +20 points)'
        # Profile completion (unchanged)
        if self.profile_complete:
            score_breakdown['profile_completion'] = 15
            score_breakdown['details']['profile_completion'] = 'Profile complete: +15 points'
        else:
            score_breakdown['details']['profile_completion'] = 'Profile incomplete: +0 points (complete your profile for +15 points)'
        # Media content (revised: counts non-test media, reduced points)
        media_count = self.media.filter(is_test_video=False).count() # Count only general portfolio media
        if media_count >= 5:
            score_breakdown['media_content'] = 15
            score_breakdown['details']['media_content'] = 'Strong portfolio (5+ general items): +15 points'
        elif media_count >= 3:
            score_breakdown['media_content'] = 10
            score_breakdown['details']['media_content'] = 'Developing portfolio (3-4 general items): +10 points'
        elif media_count >= 1:
            score_breakdown['media_content'] = 5
            score_breakdown['details']['media_content'] = 'Started portfolio (1-2 general items): +5 points'
        else:
            score_breakdown['media_content'] = 0 # Explicitly set to 0 if no media
            score_breakdown['details']['media_content'] = 'No general media: +0 points (add portfolio items for up to +15 points)'
        # Specialization (revised: increased points)
        has_specialization = self.has_specialization()
        if has_specialization:
            score_breakdown['specialization'] = 20
            score_breakdown['details']['specialization'] = 'Has at least 1 specialization: +20 points'
        else:
            score_breakdown['specialization'] = 0 # Explicitly set to 0 if no specialization
            score_breakdown['details']['specialization'] = 'No specialization: +0 points (add a specialization for +20 points)'
        # Calculate total
        score_breakdown['total'] = (
            score_breakdown['account_tier'] +
            score_breakdown['verification'] +
            score_breakdown['profile_completion'] +
            score_breakdown['media_content'] +
            score_breakdown['specialization']
        )
        score_breakdown['total'] = min(score_breakdown['total'], 100)
        # Improvement tips
        if score_breakdown['total'] < 80:
            score_breakdown['improvement_tips'] = []
            if self.account_type == 'free':
                score_breakdown['improvement_tips'].append('Upgrade to Silver (+20), Gold (+30), or Platinum (+40) for more points')
            if not self.is_verified:
                score_breakdown['improvement_tips'].append('Verify your profile for +20 points')
            if not self.profile_complete:
                score_breakdown['improvement_tips'].append('Complete your profile for +15 points')
            if media_count < 5: # media_count here still refers to general media due to earlier re-assignment
                score_breakdown['improvement_tips'].append('Add more general portfolio items for up to +15 points')
            if not has_specialization:
                score_breakdown['improvement_tips'].append('Add a specialization for +20 points')
        return score_breakdown
    
    @property
    def get_media(self):
        """
        Access the TalentMedia instances associated with this user via TalentUserProfile.
        Uses select_related to reduce database queries.
        """
        return self.media.all().select_related('talent')

    def get_image_limit(self):
        """
        Get the maximum number of images allowed based on account type.
        """
        limits = {
            'free': 2,
            'silver': 4,
            'gold': 5,
            'platinum': 6
        }
        return limits.get(self.account_type, 0)
        
    def get_video_limit(self):
        """
        Get the maximum number of videos allowed based on account type.
        """
        limits = {
            'free': 1,
            'silver': 2,
            'gold': 3,
            'platinum': 4
        }
        return limits.get(self.account_type, 0)
        
    def can_upload_image(self):
        """
        Check if the user can upload an image based on their account type.
        Uses a single database query with annotation to improve performance.
        """
        from django.db.models import Count
        # Get the current count with a single query
        image_count = getattr(self, '_image_count', None)
        if image_count is None:
            image_count = self.media.filter(media_type='image', is_test_video=False).count()
            self._image_count = image_count  # Cache the count
            
        return image_count < self.get_image_limit()

    def can_upload_video(self):
        """
        Check if the user can upload a video based on their account type.
        Uses a single database query with annotation to improve performance.
        """
        from django.db.models import Count
        # Get the current count with a single query
        video_count = getattr(self, '_video_count', None)
        if video_count is None:
            video_count = self.media.filter(media_type='video', is_test_video=False).count()
            self._video_count = video_count  # Cache the count
            
        return video_count < self.get_video_limit()
    country = models.CharField(max_length=25, null=False,default='country')
    city = models.CharField(max_length=25, null=False,default='city')
    zipcode = models.CharField(max_length=30, null=False,default="")
    phone = models.CharField(max_length=20, null=False,default="")
    date_of_birth = models.DateField(verbose_name="Date of Birth", blank=True, null=True, help_text="The user's date of birth.")
    #parental_approval = models.BooleanField(default=False, verbose_name="Parental Approval", help_text="Indicates whether parental approval has been provided for minors.")

    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES,default="Male")

    def __str__(self):
        return self.user.email
        
    @classmethod
    def with_media_counts(cls, queryset=None):
        """
        Return a queryset with annotated media counts.
        This method can be used to efficiently fetch profiles with their media counts.
        """
        from django.db.models import Count, Q
        
        queryset = queryset if queryset is not None else cls.objects.all()
        return queryset.annotate(
            _image_count=Count('media', filter=Q(media__media_type='image')),
            _video_count=Count('media', filter=Q(media__media_type='video'))
        )

class BackGroundJobsProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='background_profile'
    )
    country = models.CharField(max_length=25, null=False, default='country')
    date_of_birth = models.DateField(verbose_name="Date of Birth", blank=True, null=True)
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES,default="Male")
    
    ACCOUNT_TYPES = [
        ('back_ground_jobs', 'Background Jobs'),
        ('free', 'Free'),
    ]
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='free')

    def get_profile_score(self):
        score_breakdown = {
            'total': 0,
            'account_tier': 50,  # All accounts are paid, flat 50 points
            'profile_completion': 0,
            'item_diversity': 0,
            'item_quantity': 0,
            'details': {}
        }
        score_breakdown['details']['account_tier'] = 'All accounts paid: +50 points'
        # Profile completion: 15 points for filling basic fields
        profile_complete = bool(self.country and self.date_of_birth and self.gender)
        if profile_complete:
            score_breakdown['profile_completion'] = 15
            score_breakdown['details']['profile_completion'] = 'Profile complete: +15 points'
        else:
            score_breakdown['details']['profile_completion'] = 'Profile incomplete: +0 points (complete your profile for +15 points)'
        # Item diversity: 5 points per item type
        item_types = [
            Prop.objects.filter(BackGroundJobsProfile=self).exists(),
            Costume.objects.filter(BackGroundJobsProfile=self).exists(),
            Location.objects.filter(BackGroundJobsProfile=self).exists(),
            Memorabilia.objects.filter(BackGroundJobsProfile=self).exists(),
            Vehicle.objects.filter(BackGroundJobsProfile=self).exists(),
            ArtisticMaterial.objects.filter(BackGroundJobsProfile=self).exists(),
            MusicItem.objects.filter(BackGroundJobsProfile=self).exists(),
            RareItem.objects.filter(BackGroundJobsProfile=self).exists()
        ]
        item_type_count = sum(1 for t in item_types if t)
        score_breakdown['item_diversity'] = item_type_count * 5
        if item_type_count > 0:
            score_breakdown['details']['item_diversity'] = f'{item_type_count} item types: +{item_type_count * 5} points'
        else:
            score_breakdown['details']['item_diversity'] = 'No item types: +0 points (add different item types for +5 points each)'
        # Item quantity: Up to 25 points based on total items
        total_items = sum([
            Prop.objects.filter(BackGroundJobsProfile=self).count(),
            Costume.objects.filter(BackGroundJobsProfile=self).count(),
            Location.objects.filter(BackGroundJobsProfile=self).count(),
            Memorabilia.objects.filter(BackGroundJobsProfile=self).count(),
            Vehicle.objects.filter(BackGroundJobsProfile=self).count(),
            ArtisticMaterial.objects.filter(BackGroundJobsProfile=self).count(),
            MusicItem.objects.filter(BackGroundJobsProfile=self).count(),
            RareItem.objects.filter(BackGroundJobsProfile=self).count()
        ])
        if total_items > 20:
            score_breakdown['item_quantity'] = 25
            score_breakdown['details']['item_quantity'] = 'Large collection (20+ items): +25 points'
        elif total_items > 10:
            score_breakdown['item_quantity'] = 20
            score_breakdown['details']['item_quantity'] = 'Medium collection (10-20 items): +20 points'
        elif total_items > 5:
            score_breakdown['item_quantity'] = 15
            score_breakdown['details']['item_quantity'] = 'Small collection (5-10 items): +15 points'
        elif total_items > 0:
            score_breakdown['item_quantity'] = 10
            score_breakdown['details']['item_quantity'] = 'Starter collection (1-5 items): +10 points'
        else:
            score_breakdown['details']['item_quantity'] = 'No items: +0 points (add items for up to +25 points)'
        # Calculate total
        score_breakdown['total'] = (
            score_breakdown['account_tier'] +
            score_breakdown['profile_completion'] +
            score_breakdown['item_diversity'] +
            score_breakdown['item_quantity']
        )
        score_breakdown['total'] = min(score_breakdown['total'], 100)
        # Improvement tips
        if score_breakdown['total'] < 80:
            score_breakdown['improvement_tips'] = []
            if not profile_complete:
                score_breakdown['improvement_tips'].append('Complete your profile for +15 points')
            if item_type_count < 8:
                score_breakdown['improvement_tips'].append('Add more item types for +5 points each')
            if total_items < 5:
                score_breakdown['improvement_tips'].append('Add more items for up to +25 points')
        return score_breakdown

    def __str__(self):
        return f"Background Profile - {self.user.email}"






def get_user_media(self):
        """
        Fetch all media associated with the user's talent account.
        """
        if self.talentaccount:
            return self.talentaccount.media.all()
        return TalentMedia.objects.none()    


# to handle media file 
def user_media_path(instance, filename):
    """
    Save files in a user-specific directory within talent_media folder.
    """
    return f"talent_media/user_{instance.talent.user.id}/{filename}" 


def unique_user_media_path(instance, filename):
    """
    Save files in a user-specific directory with a unique file name.
    """
    ext = filename.split('.')[-1]  # Get the file extension
    unique_name = f"{uuid.uuid4().hex}.{ext}"  # Generate a unique name
    return os.path.join('talent_media', unique_name)


class TalentMedia(models.Model):
    talent = models.ForeignKey(TalentUserProfile, on_delete=models.CASCADE, related_name='media')
    name = models.CharField(max_length=124, blank=False, null=False, default="Untitled Media")
    media_info = models.TextField(max_length=160, blank=False, null=False)
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    media_file = models.FileField(upload_to=user_media_path)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_of_birth = models.DateField(verbose_name="Date of Birth", blank=True, null=True, help_text="The user's date of birth.")
    # New fields for test video logic
    is_test_video = models.BooleanField(default=False, help_text="Is this a required test video for actor/comparse?")
    test_video_number = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Test video order (1-5)")
    # New: Special flag for the 1-minute 'about yourself' video
    is_about_yourself_video = models.BooleanField(default=False, help_text="Is this the 1-minute 'about yourself' video?")

    def _get_video_duration(self, file_path):
        """
        Returns the duration of the video in seconds using ffprobe (from ffmpeg).
        Returns None if ffprobe is not available or fails.
        """
        import subprocess
        import json
        import shutil
        
        # Check if ffprobe is available
        if not shutil.which('ffprobe'):
            print("Warning: ffprobe not found. Video duration validation disabled.")
            return None
            
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'json', file_path
            ], capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            return duration
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return None

    def _is_ffmpeg_available(self):
        """Check if FFmpeg is available on the system"""
        import shutil
        return shutil.which('ffprobe') is not None

    def save(self, *args, **kwargs):
        # Validate file size limits using centralized validation
        if self.media_file and not self.pk:  # Only check for new uploads
            from .utils.file_validators import validate_video_file, validate_image_file
            
            try:
                if self.media_type == 'video':
                    validate_video_file(self.media_file)
                elif self.media_type == 'image':
                    validate_image_file(self.media_file)
            except Exception as e:
                raise ValidationError(str(e))
        
        # Enforce test video rules for actor/comparse/host and about_yourself_video for all
        if self.is_test_video and self.media_type == 'video':
            # Check if user has any specialization
            has_visual = hasattr(self.talent, 'visual_worker')
            has_expressive = hasattr(self.talent, 'expressive_worker')
            has_hybrid = hasattr(self.talent, 'hybrid_worker')
            
            if not (has_visual or has_expressive or has_hybrid):
                raise ValidationError("Test videos can only be uploaded by users with specializations.")
            
            # About yourself video (test_video_number=5) is allowed for all specializations
            if self.is_about_yourself_video and self.test_video_number == 5:
                # Count existing about_yourself videos
                about_videos = TalentMedia.objects.filter(
                    talent=self.talent, 
                    is_test_video=True, 
                    is_about_yourself_video=True
                )
                if self.pk is None and about_videos.count() >= 1:
                    raise ValidationError("You can only upload 1 about yourself video.")
            
            # Regular test videos (1-4) only for specific ExpressiveWorker types
            elif not self.is_about_yourself_video and 1 <= (self.test_video_number or 0) <= 4:
                performer_type = None
                try:
                    performer_type = self.talent.expressive_worker.performer_type
                except Exception:
                    pass
                
                if performer_type not in ['actor', 'comparse', 'host']:
                    raise ValidationError("Test videos (1-4) are only allowed for actors, comparse, or hosts.")
                
                # Count existing test videos for this user (excluding about_yourself)
                test_videos = TalentMedia.objects.filter(
                    talent=self.talent, 
                    is_test_video=True, 
                    is_about_yourself_video=False
                )
                if self.pk is None and test_videos.count() >= 4:
                    raise ValidationError("You can only upload 4 test videos.")
            
            # Duration validation (only if FFmpeg is available)
            if self.media_file and self._is_ffmpeg_available():
                temp_path = None
                try:
                    # Save to temp file
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                        for chunk in self.media_file.chunks():
                            tmp.write(chunk)
                        temp_path = tmp.name
                    duration = self._get_video_duration(temp_path)
                    if duration is not None:  # Only validate if we could get duration
                        # Duration validation
                        if self.is_about_yourself_video:
                            # About yourself video must be ~60s
                            if not (58 <= duration <= 62):
                                raise ValidationError("About yourself video must be about 60 seconds.")
                        else:
                            # Regular test videos must be ~30s
                            if not (28 <= duration <= 32):
                                raise ValidationError("Test videos must be about 30 seconds.")
                    # If duration is None (FFmpeg failed), we skip validation but log a warning
                    elif duration is None:
                        print(f"Warning: Could not validate duration for video {self.name}. FFmpeg may not be properly configured.")
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.unlink(temp_path)
            elif self.media_file and not self._is_ffmpeg_available():
                print("Warning: FFmpeg not available. Video duration validation skipped.")
        
        # Process media file before saving
        if self.media_file and not self.pk:  # Only process new uploads
            try:
                # For images, process immediately
                if self.media_type == 'image':
                    # Process the image file
                    processed_path = MediaProcessor.process_media(self.media_file)
                
                    if processed_path:
                        # Save the processed file
                        with open(processed_path, 'rb') as f:
                            self.media_file.save(
                                os.path.basename(self.media_file.name),
                                ContentFile(f.read()),
                                save=False
                            )
                        
                        # Clean up temporary files
                        os.unlink(processed_path)
                
                # For videos, use the queue system to prevent server overload
                elif self.media_type == 'video':
                    # Save the original file temporarily for processing
                    # The actual processing will happen after the model is saved
                    # via the post_save signal handler
                    pass  # Video processing will be handled in post_save
                    
            except Exception as e:
                print(f"Error processing media: {str(e)}")
        
        super().save(*args, **kwargs)
    
    def _generate_video_thumbnail(self, video_path):
        """
        Generate a thumbnail from a video file.
        Returns None if FFmpeg is not available.
        """
        # Check if FFmpeg is available
        if not self._is_ffmpeg_available():
            print("Warning: FFmpeg not available. Skipping video thumbnail generation.")
            return None
        
        try:
            thumbnail_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', '00:00:01',  # Take frame at 1 second
                '-vframes', '1',
                '-q:v', '2',
                thumbnail_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            return thumbnail_path
            
        except Exception as e:
            print(f"Error generating video thumbnail: {str(e)}")
            return None

    def __str__(self):
        return f"{self.talent.user.username}'s {self.media_type} - {self.media_file.name}"
   

# Signal handler for video processing
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils.video_queue import enqueue_video_processing

@receiver(post_save, sender=TalentMedia)
def process_video_after_save(sender, instance, created, **kwargs):
    """Process video files asynchronously after the model is saved"""
    if created and instance.media_type == 'video':
        # Check if FFmpeg is available before attempting video processing
        if not instance._is_ffmpeg_available():
            print(f"Warning: FFmpeg not available. Skipping video processing for {instance.name}. Video will be used as-is.")
            return
        
        # Enqueue the video for processing
        def video_processing_callback(task):
            if task.status == 'completed':
                try:
                    # Get the processed video path from the task result
                    processed_path = task.result
                    if processed_path:
                        # Update the media file with the processed version
                        with open(processed_path, 'rb') as f:
                            instance.media_file.save(
                                os.path.basename(instance.media_file.name),
                                ContentFile(f.read()),
                                save=False
                            )
                        
                        # Generate thumbnail
                        thumbnail_path = instance._generate_video_thumbnail(processed_path)
                        if thumbnail_path:
                            with open(thumbnail_path, 'rb') as f:
                                instance.thumbnail.save(
                                    f"{os.path.splitext(instance.media_file.name)[0]}_thumb.jpg",
                                    ContentFile(f.read()),
                                    save=False
                                )
                        
                        # Save the instance with the processed file and thumbnail
                        instance.save(update_fields=['media_file', 'thumbnail'])
                        
                        # Clean up temporary files
                        os.unlink(processed_path)
                        if thumbnail_path and os.path.exists(thumbnail_path):
                            os.unlink(thumbnail_path)
                    else:
                        # Processing returned None (likely due to missing FFmpeg)
                        print(f"Video processing returned None for {instance.name}. Video will be used as-is.")
                except Exception as e:
                    print(f"Error updating video after processing: {str(e)}")
            elif task.status == 'failed':
                print(f"Video processing failed for {instance.name}: {task.error}")
        
        # Enqueue the video processing task
        enqueue_video_processing(instance.id, callback=video_processing_callback)


    #socil media links
class SocialMediaLinks(models.Model):
    user = models.OneToOneField(TalentUserProfile, on_delete=models.CASCADE, related_name='social_media_links')
    facebook = models.URLField(blank=True, null=True, verbose_name="Facebook URL")
    twitter = models.URLField(blank=True, null=True, verbose_name="Twitter URL")
    instagram = models.URLField(blank=True, null=True, verbose_name="Instagram URL")
    linkedin = models.URLField(blank=True, null=True, verbose_name="LinkedIn URL")
    youtube = models.URLField(blank=True, null=True, verbose_name="YouTube URL")
    tiktok = models.URLField(blank=True, null=True, verbose_name="TikTok URL")
    snapchat = models.URLField(blank=True, null=True, verbose_name="Snapchat URL")

    def get_user_links(self):
        """Return all social media links as a dictionary"""
        return {
            'facebook': self.facebook,
            'twitter': self.twitter,
            'instagram': self.instagram,
            'linkedin': self.linkedin,
            'youtube': self.youtube,
            'tiktok': self.tiktok,
            'snapchat': self.snapchat
        }

    def has_social_media_links(self):
        return any([self.facebook, self.twitter, self.instagram, self.linkedin, self.youtube, self.tiktok, self.snapchat])
        
    def __str__(self):
        return f"Social Media Links: {self.user.username}"











class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    BackGroundJobsProfile = models.ForeignKey(
        BackGroundJobsProfile,
        on_delete=models.CASCADE,
        related_name='%(class)s_items',  # Dynamically generates unique related_name
    null=True,blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    genre = models.ForeignKey(
        Genre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_items'  # Dynamically generates unique related_name
    )
    is_for_rent = models.BooleanField(default=False)
    is_for_sale = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='item_images/')

    class Meta:
        abstract = True  # This makes it an abstract base class

    def __str__(self):
        return self.name
class Prop(Item):
    material = models.CharField(max_length=255, blank=True, null=True)
    used_in_movie = models.CharField(max_length=255, blank=True, null=True)
    condition = models.CharField(max_length=255, blank=True, null=True)

class Costume(Item):
    size = models.CharField(max_length=50, blank=True, null=True)
    worn_by = models.CharField(max_length=255, blank=True, null=True)
    era = models.CharField(max_length=255, blank=True, null=True)

class Location(Item):
    address = models.CharField(max_length=255, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    is_indoor = models.BooleanField(default=True)

class Memorabilia(Item):
    signed_by = models.CharField(max_length=255, blank=True, null=True)
    authenticity_certificate = models.FileField(upload_to='certificates/', blank=True, null=True)

class Vehicle(Item):
    make = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)

class ArtisticMaterial(Item):
    type = models.CharField(max_length=255, blank=True, null=True)
    condition = models.CharField(max_length=255, blank=True, null=True)

class MusicItem(Item):
    instrument_type = models.CharField(max_length=255, blank=True, null=True)
    used_by = models.CharField(max_length=255, blank=True, null=True)

class RareItem(Item):
    provenance = models.TextField(blank=True, null=True)
    is_one_of_a_kind = models.BooleanField(default=False)


# Function to handle band media file paths
def band_media_path(instance, filename):
    """
    Save files in a band-specific directory within band_media folder.
    """
    return f"band_media/band_{instance.band.id}/{filename}"

# Band model for talent users to form groups
class Band(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # The creator/admin of the band
    creator = models.ForeignKey(TalentUserProfile, on_delete=models.CASCADE, related_name='created_bands')
    
    # Members of the band (many-to-many relationship with TalentUserProfile)
    members = models.ManyToManyField(TalentUserProfile, through='BandMembership', related_name='bands')
    
    # Band type
    BAND_TYPE_CHOICES = [
        ('musical', 'Musical Bands/Troupes'),
        ('theatrical', 'Theatrical Troupes'),
        ('stunt', 'Stunt/Performance Teams'),
        ('dance', 'Dance Troupes'),
        ('event', 'Event Squads'),
    ]
    band_type = models.CharField(max_length=20, choices=BAND_TYPE_CHOICES, default='musical')
    

    # Band profile picture
    profile_picture = models.ImageField(upload_to='band_profile_pictures/', blank=True, null=True)
    
    # Band contact information
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Band location
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # Band website and social media
    website = models.URLField(blank=True, null=True)
    
    def has_bands_subscription(self):
        """Check if the band creator has an active bands subscription"""
        from payments.models import Subscription
        return Subscription.objects.filter(
            user=self.creator.user,
            plan__name='bands',
            is_active=True,
            status='active'
        ).exists()
    
    def get_profile_score(self):
        score_breakdown = {
            'total': 0,
            'profile_completion': 0,
            'media_content': 0,
            'member_count': 0,
            'band_details': 0,
            'details': {}
        }
        # Profile completion: Up to 30 points based on % of fields completed
        profile_fields = [
            bool(self.name), bool(self.description), bool(self.band_type), 
            bool(self.profile_picture), bool(self.contact_email or self.contact_phone), 
            bool(self.location)
        ]
        completed_fields = sum(1 for f in profile_fields if f)
        profile_percent = (completed_fields / len(profile_fields)) * 100
        if profile_percent == 100:
            score_breakdown['profile_completion'] = 30
            score_breakdown['details']['profile_completion'] = 'Complete band profile: +30 points'
        elif profile_percent >= 75:
            score_breakdown['profile_completion'] = 20
            score_breakdown['details']['profile_completion'] = 'Mostly complete band profile: +20 points'
        elif profile_percent >= 50:
            score_breakdown['profile_completion'] = 10
            score_breakdown['details']['profile_completion'] = 'Partially complete band profile: +10 points'
        else:
            score_breakdown['details']['profile_completion'] = 'Minimal band profile: +0 points (complete your band profile for up to +30 points)'
        # Media content: Up to 30 points based on quantity
        media_count = self.media.count()
        if media_count >= 6:
            score_breakdown['media_content'] = 30
            score_breakdown['details']['media_content'] = 'Maximum media (6 items): +30 points'
        elif media_count >= 4:
            score_breakdown['media_content'] = 20
            score_breakdown['details']['media_content'] = 'Good media (4-5 items): +20 points'
        elif media_count >= 2:
            score_breakdown['media_content'] = 10
            score_breakdown['details']['media_content'] = 'Basic media (2-3 items): +10 points'
        elif media_count == 1:
            score_breakdown['media_content'] = 5
            score_breakdown['details']['media_content'] = 'Minimal media (1 item): +5 points'
        else:
            score_breakdown['details']['media_content'] = 'No media: +0 points (add media for up to +30 points)'
        # Member count: Up to 30 points based on number of members
        member_count = self.member_count
        if member_count >= 10:
            score_breakdown['member_count'] = 30
            score_breakdown['details']['member_count'] = 'Large band (10+ members): +30 points'
        elif member_count >= 5:
            score_breakdown['member_count'] = 20
            score_breakdown['details']['member_count'] = 'Medium band (5-9 members): +20 points'
        elif member_count >= 3:
            score_breakdown['member_count'] = 10
            score_breakdown['details']['member_count'] = 'Small band (3-4 members): +10 points'
        elif member_count > 0:
            score_breakdown['member_count'] = 5
            score_breakdown['details']['member_count'] = 'Minimal band (1-2 members): +5 points'
        else:
            score_breakdown['details']['member_count'] = 'No members: +0 points (add members for up to +30 points)'
        # Band details: Up to 10 points for member positions
        members_with_positions = BandMembership.objects.filter(band=self, position__isnull=False).exclude(position='').count()
        if members_with_positions == member_count and member_count > 0:
            score_breakdown['band_details'] = 10
            score_breakdown['details']['band_details'] = 'All members have positions: +10 points'
        elif members_with_positions > 0:
            score_breakdown['band_details'] = 5
            score_breakdown['details']['band_details'] = 'Some members have positions: +5 points'
        else:
            score_breakdown['details']['band_details'] = 'No member positions: +0 points (add positions for up to +10 points)'
        # Calculate total
        score_breakdown['total'] = (
            score_breakdown['profile_completion'] +
            score_breakdown['media_content'] +
            score_breakdown['member_count'] +
            score_breakdown['band_details']
        )
        score_breakdown['total'] = min(score_breakdown['total'], 100)
        # Improvement tips
        if score_breakdown['total'] < 80:
            score_breakdown['improvement_tips'] = []
            if profile_percent < 100:
                score_breakdown['improvement_tips'].append('Complete your band profile for up to +30 points')
            if media_count < 6:
                score_breakdown['improvement_tips'].append('Add more media for up to +30 points')
            if member_count < 5:
                score_breakdown['improvement_tips'].append('Add more members for up to +30 points')
            if members_with_positions < member_count:
                score_breakdown['improvement_tips'].append('Add positions for all members for up to +10 points')
        return score_breakdown
    
    @property
    def member_count(self):
        """Get the total number of members in the band
        Uses caching to reduce database queries.
        """
        if not hasattr(self, '_member_count'):
            self._member_count = self.bandmembership_set.count()
        return self._member_count
    
    @property
    def admin_count(self):
        """Get the number of admin members in the band
        Uses caching to reduce database queries.
        """
        if not hasattr(self, '_admin_count'):
            self._admin_count = self.bandmembership_set.filter(role='admin').count()
        return self._admin_count
        
    @classmethod
    def with_counts(cls, queryset=None):
        """Return a queryset with annotated member and admin counts.
        This method can be used to efficiently fetch bands with their counts.
        """
        from django.db.models import Count, Q
        
        queryset = queryset if queryset is not None else cls.objects.all()
        return queryset.annotate(
            _member_count=Count('bandmembership'),
            _admin_count=Count('bandmembership', filter=Q(bandmembership__role='admin'))
        )
    
    def get_max_admins(self):
        """Calculate the maximum number of admins allowed based on member count"""
        count = self.member_count
        if count >= 25:
            return 3  # 3 admins for bands with 25+ members
        elif count >= 5:
            return 2  # 2 admins for bands with 5-24 members
        else:
            return 1  # 1 admin for bands with less than 5 members
    
    def can_add_admin(self):
        """Check if another admin can be added to the band"""
        return self.admin_count < self.get_max_admins()
    
    def __str__(self):
        return self.name

# Through model for Band and TalentUserProfile many-to-many relationship
class BandMembership(models.Model):
    talent_user = models.ForeignKey(TalentUserProfile, on_delete=models.CASCADE)
    band = models.ForeignKey(Band, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    
    # Member's position in the band (e.g., vocalist, guitarist, etc.)
    position = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        unique_together = ('talent_user', 'band')
        
    def __str__(self):
        return f"{self.talent_user.user.username} - {self.band.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        # Check if this is a new membership or role is being changed to admin
        is_new = self.pk is None
        if is_new or (not is_new and self.role == 'admin'):
            # Use cached counts if available or fetch with a single query
            admin_count = getattr(self.band, '_admin_count', None)
            member_count = getattr(self.band, '_member_count', None)
            
            if admin_count is None:
                admin_count = BandMembership.objects.filter(band=self.band, role='admin').count()
                
            if member_count is None:
                member_count = BandMembership.objects.filter(band=self.band).count()
            
            # Adjust counts based on current operation
            if not is_new and self.role == 'admin':
                # Check if the role was already admin
                try:
                    old_instance = BandMembership.objects.get(pk=self.pk)
                    if old_instance.role != 'admin':
                        # Role is changing to admin, so increment the count
                        admin_count += 1
                except BandMembership.DoesNotExist:
                    pass
            else:
                # New membership with admin role
                if is_new:
                    member_count += 1  # Include this new membership
                    if self.role == 'admin':
                        admin_count += 1
            
            # Get max admins directly from the helper method
            max_admins = 1  # Default
            if member_count >= 25:
                max_admins = 3
            elif member_count >= 5:
                max_admins = 2
            
            # Enforce admin limit
            if admin_count > max_admins:
                from django.core.exceptions import ValidationError
                raise ValidationError(f"This band can have a maximum of {max_admins} admins based on its size ({member_count} members).")
        
        result = super().save(*args, **kwargs)
        
        # Invalidate cached counts after saving
        if hasattr(self.band, '_admin_count'):
            delattr(self.band, '_admin_count')
        if hasattr(self.band, '_member_count'):
            delattr(self.band, '_member_count')
            
        return result


# BandMedia model for storing band media files (images and videos)
class BandMedia(models.Model):
    band = models.ForeignKey(Band, on_delete=models.CASCADE, related_name='media')
    name = models.CharField(max_length=124, blank=False, null=False, default="Untitled Media")
    media_info = models.TextField(max_length=160, blank=False, null=False)
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    media_file = models.FileField(upload_to=band_media_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        """
        Validate upload limits before saving the instance.
        Optimized to reduce database queries.
        """
        # Only validate for new instances
        if self.pk is None:
            # Cache media counts to avoid repeated queries
            image_count = getattr(self.band, '_band_image_count', None)
            video_count = getattr(self.band, '_band_video_count', None)
            
            if self.media_type == 'image':
                if image_count is None:
                    image_count = self.band.media.filter(media_type='image').count()
                    self.band._band_image_count = image_count
                    
                if image_count >= 5:
                    raise ValidationError("A band can have a maximum of 5 images.")
            
            elif self.media_type == 'video':
                if video_count is None:
                    video_count = self.band.media.filter(media_type='video').count()
                    self.band._band_video_count = video_count
                    
                if video_count >= 5:
                    raise ValidationError("A band can have a maximum of 5 videos.")
    
    def save(self, *args, **kwargs):
        self.clean()  # Run validation before saving
        result = super().save(*args, **kwargs)
        
        # Invalidate cached counts after saving
        if hasattr(self.band, '_band_image_count'):
            delattr(self.band, '_band_image_count')
        if hasattr(self.band, '_band_video_count'):
            delattr(self.band, '_band_video_count')
            
        return result
    
    def __str__(self):
        return f"{self.band.name}'s {self.media_type} - {self.media_file.name}"

# Band Invitation model for time-limited invitation codes
class BandInvitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    band = models.ForeignKey(Band, on_delete=models.CASCADE, related_name='invitations')
    created_by = models.ForeignKey(TalentUserProfile, on_delete=models.CASCADE, related_name='created_invitations')
    invitation_code = models.CharField(max_length=8, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(TalentUserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_invitations')
    position = models.CharField(max_length=100, blank=True, null=True)  # Optional position in the band
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    @classmethod
    def generate_invitation_code(cls):
        """Generate a random 8-character alphanumeric code"""
        import random
        import string
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(characters, k=8))
            # Check if code already exists
            if not cls.objects.filter(invitation_code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        # Generate invitation code if not provided
        if not self.invitation_code:
            self.invitation_code = self.generate_invitation_code()
        
        # Set expiration time if not provided (15 minutes from now)
        if not self.expires_at:
            from django.utils import timezone
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(minutes=15)
        
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if the invitation is still valid"""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()
    
    def __str__(self):
        return f"Invitation to {self.band.name} - {self.invitation_code}"




class VisualWorker(models.Model):
    profile = models.OneToOneField(TalentUserProfile, on_delete=models.CASCADE, related_name='visual_worker')
    PRIMARY_CATEGORIES = [
        ('photographer', 'Photographer'), ('cinematographer', 'Cinematographer'),
        ('director', 'Director'), ('editor', 'Video/Film Editor'),
        ('animator', 'Animator'), ('graphic_designer', 'Graphic Designer'),
        ('makeup_artist', 'Makeup Artist'), ('costume_designer', 'Costume Designer'),
        ('set_designer', 'Set Designer'), ('lighting_designer', 'Lighting Designer'),
        ('visual_artist', 'Visual Artist'), ('composer', 'Music Composer'),
        ('sound_designer', 'Sound Designer'), ('other', 'Other Visual Creator')
    ]
    primary_category = models.CharField(max_length=50, choices=PRIMARY_CATEGORIES, default='photographer')
    years_experience = models.PositiveIntegerField(default=0)
    EXPERIENCE_LEVEL = [
        ('beginner', 'Beginner'), ('intermediate', 'Intermediate'),
        ('professional', 'Professional'), ('expert', 'Expert')
    ]
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL, default='beginner')
    portfolio_link = models.URLField(blank=True, null=True)
    AVAILABILITY_CHOICES = [
        ('full_time', 'Full Time'), ('part_time', 'Part Time'),
        ('weekends', 'Weekends Only'), ('flexible', 'Flexible')
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='full_time')
    RATE_RANGES = [
        ('low', 'Budget Friendly'), ('mid', 'Mid-Range'),
        ('high', 'Premium'), ('negotiable', 'Negotiable')
    ]
    rate_range = models.CharField(max_length=20, choices=RATE_RANGES, default='low')
    willing_to_relocate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    face_picture = models.ImageField(upload_to='profile_pictures/face/', null=True, blank=True)
    mid_range_picture = models.ImageField(upload_to='profile_pictures/mid/', null=True, blank=True)
    full_body_picture = models.ImageField(upload_to='profile_pictures/full/', null=True, blank=True)

class ExpressiveWorker(models.Model):
    profile = models.OneToOneField(TalentUserProfile, on_delete=models.CASCADE, related_name='expressive_worker')
    PERFORMER_TYPES = [
        ('actor', 'Actor'),('comparse','Comparse'),('voice_actor', 'Voice Actor'),
        ('singer', 'Singer'), ('dancer', 'Dancer'),
        ('musician', 'Musician'), ('comedian', 'Comedian'),
        ('host', 'TV/Event Host'), ('narrator', 'Narrator'),
        ('puppeteer', 'Puppeteer'), ('other', 'Other Performer')
    ]
    performer_type = models.CharField(max_length=50, choices=PERFORMER_TYPES, default='actor')
    years_experience = models.PositiveIntegerField(default=0)
    height = models.FloatField(default=0.0, help_text="Height in cm")
    weight = models.FloatField(default=0.0, help_text="Weight in kg")
    HAIR_COLORS = [('blonde', 'Blonde'), ('brown', 'Brown'), ('black', 'Black'), 
                   ('red', 'Red'), ('gray', 'Gray/Silver'), ('other', 'Other')]
    hair_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown')
    # New: Hair type
    HAIR_TYPES = [
        ('straight', 'Straight'), ('wavy', 'Wavy'), ('curly', 'Curly'), ('coily', 'Coily'), ('bald', 'Bald'), ('other', 'Other')
    ]
    hair_type = models.CharField(max_length=20, choices=HAIR_TYPES, default='straight')
    # New: Skin tone (reuse HybridWorker's choices)
    SKIN_TONES = [
        ('fair', 'Fair'), ('light', 'Light'), ('medium', 'Medium'), 
        ('olive', 'Olive'), ('brown', 'Brown'), ('dark', 'Dark')
    ]
    skin_tone = models.CharField(max_length=20, choices=SKIN_TONES, default='fair')
    EYE_COLORS = [('blue', 'Blue'), ('green', 'Green'), ('brown', 'Brown'), 
                  ('hazel', 'Hazel'), ('black', 'Black'), ('other', 'Other')]
    eye_color = models.CharField(max_length=20, choices=EYE_COLORS, default='brown')
    # New: Eye size
    EYE_SIZES = [
        ('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')
    ]
    eye_size = models.CharField(max_length=10, choices=EYE_SIZES, default='medium')
    # New: Eye pattern
    EYE_PATTERNS = [
        ('normal', 'Normal'), ('protruding', 'Protruding'), ('sunken', 'Sunken'), ('almond', 'Almond'), ('round', 'Round'), ('other', 'Other')
    ]
    eye_pattern = models.CharField(max_length=20, choices=EYE_PATTERNS, default='normal')
    # New: Face shape
    FACE_SHAPES = [
        ('oval', 'Oval'), ('round', 'Round'), ('square', 'Square'), ('heart', 'Heart'), ('diamond', 'Diamond'), ('long', 'Long'), ('other', 'Other')
    ]
    face_shape = models.CharField(max_length=20, choices=FACE_SHAPES, default='oval')
    # New: Forehead shape
    FOREHEAD_SHAPES = [
        ('broad', 'Broad'), ('narrow', 'Narrow'), ('rounded', 'Rounded'), ('straight', 'Straight'), ('other', 'Other')
    ]
    forehead_shape = models.CharField(max_length=20, choices=FOREHEAD_SHAPES, default='straight')
    # New: Lip shape
    LIP_SHAPES = [
        ('thin', 'Thin'), ('full', 'Full'), ('heart', 'Heart-shaped'), ('round', 'Round'), ('bow', 'Cupid\'s Bow'), ('other', 'Other')
    ]
    lip_shape = models.CharField(max_length=20, choices=LIP_SHAPES, default='full')
    # New: Eyebrow pattern
    EYEBROW_PATTERNS = [
        ('arched', 'Arched'), ('straight', 'Straight'), ('curved', 'Curved'), ('thick', 'Thick'), ('thin', 'Thin'), ('other', 'Other')
    ]
    eyebrow_pattern = models.CharField(max_length=20, choices=EYEBROW_PATTERNS, default='straight')
    # New: Beard color
    BEARD_COLORS = HAIR_COLORS
    beard_color = models.CharField(max_length=20, choices=BEARD_COLORS, default='brown', blank=True, null=True)
    # New: Beard length
    BEARD_LENGTHS = [
        ('none', 'None'), ('stubble', 'Stubble'), ('short', 'Short'), ('medium', 'Medium'), ('long', 'Long'), ('other', 'Other')
    ]
    beard_length = models.CharField(max_length=10, choices=BEARD_LENGTHS, default='none', blank=True, null=True)
    # New: Mustache color
    mustache_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown', blank=True, null=True)
    # New: Mustache length
    mustache_length = models.CharField(max_length=10, choices=BEARD_LENGTHS, default='none', blank=True, null=True)
    # New: Distinctive facial marks
    FACIAL_MARKS = [
        ('none', 'None'), ('mole', 'Mole'), ('scar', 'Scar'), ('birthmark', 'Birthmark'), ('freckles', 'Freckles'), ('other', 'Other')
    ]
    distinctive_facial_marks = models.CharField(max_length=20, choices=FACIAL_MARKS, default='none', blank=True, null=True)
    # New: Distinctive body marks
    BODY_MARKS = [
        ('none', 'None'), ('tattoo', 'Tattoo'), ('scar', 'Scar'), ('birthmark', 'Birthmark'), ('other', 'Other')
    ]
    distinctive_body_marks = models.CharField(max_length=20, choices=BODY_MARKS, default='none', blank=True, null=True)
    # New: Voice type
    VOICE_TYPES = [
        ('normal', 'Normal'), ('thin', 'Thin'), ('rough', 'Rough'), ('deep', 'Deep'), ('soft', 'Soft'), ('nasal', 'Nasal'), ('other', 'Other')
    ]
    voice_type = models.CharField(max_length=20, choices=VOICE_TYPES, default='normal')
    BODY_TYPES = [('athletic', 'Athletic'), ('slim', 'Slim'), ('muscular', 'Muscular'), 
                  ('average', 'Average'), ('plus_size', 'Plus Size'), ('other', 'Other')]
    body_type = models.CharField(max_length=20, choices=BODY_TYPES, default='average')
    AVAILABILITY_CHOICES = [
        ('full_time', 'Full Time'), ('part_time', 'Part Time'),
        ('evenings', 'Evenings Only'), ('weekends', 'Weekends Only')
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='full_time')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    face_picture = models.ImageField(upload_to='profile_pictures/face/', null=True, blank=True)
    mid_range_picture = models.ImageField(upload_to='profile_pictures/mid/', null=True, blank=True)
    full_body_picture = models.ImageField(upload_to='profile_pictures/full/', null=True, blank=True)

class HybridWorker(models.Model):
    profile = models.OneToOneField(TalentUserProfile, on_delete=models.CASCADE, related_name='hybrid_worker')
    HYBRID_TYPES = [
        ('model', 'Fashion/Commercial Model'), ('stunt_performer', 'Stunt Performer'),
        ('body_double', 'Body Double'), ('motion_capture', 'Motion Capture Artist'),
        ('background_actor', 'Background Actor'), ('specialty_performer', 'Specialty Performer'),
        ('other', 'Other Physical Performer'),
    ]
    hybrid_type = models.CharField(max_length=50, choices=HYBRID_TYPES, default='model')
    years_experience = models.PositiveIntegerField(default=0)
    height = models.FloatField(default=0.0, help_text="Height in cm")
    weight = models.FloatField(default=0.0, help_text="Weight in kg")
    
    # Hair characteristics
    HAIR_COLORS = [('blonde', 'Blonde'), ('brown', 'Brown'), ('black', 'Black'), 
                   ('red', 'Red'), ('gray', 'Gray/Silver'), ('other', 'Other')]
    hair_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown')
    HAIR_TYPES = [
        ('straight', 'Straight'), ('wavy', 'Wavy'), ('curly', 'Curly'), ('coily', 'Coily'), ('bald', 'Bald'), ('other', 'Other')
    ]
    hair_type = models.CharField(max_length=20, choices=HAIR_TYPES, default='straight')
    
    # Eye characteristics
    EYE_COLORS = [('blue', 'Blue'), ('green', 'Green'), ('brown', 'Brown'), 
                  ('hazel', 'Hazel'), ('black', 'Black'), ('other', 'Other')]
    eye_color = models.CharField(max_length=20, choices=EYE_COLORS, default='brown')
    EYE_SIZES = [
        ('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')
    ]
    eye_size = models.CharField(max_length=10, choices=EYE_SIZES, default='medium')
    EYE_PATTERNS = [
        ('normal', 'Normal'), ('protruding', 'Protruding'), ('sunken', 'Sunken'), ('almond', 'Almond'), ('round', 'Round'), ('other', 'Other')
    ]
    eye_pattern = models.CharField(max_length=20, choices=EYE_PATTERNS, default='normal')
    
    # Facial characteristics
    FACE_SHAPES = [
        ('oval', 'Oval'), ('round', 'Round'), ('square', 'Square'), ('heart', 'Heart'), ('diamond', 'Diamond'), ('long', 'Long'), ('other', 'Other')
    ]
    face_shape = models.CharField(max_length=20, choices=FACE_SHAPES, default='oval')
    FOREHEAD_SHAPES = [
        ('broad', 'Broad'), ('narrow', 'Narrow'), ('rounded', 'Rounded'), ('straight', 'Straight'), ('other', 'Other')
    ]
    forehead_shape = models.CharField(max_length=20, choices=FOREHEAD_SHAPES, default='straight')
    LIP_SHAPES = [
        ('thin', 'Thin'), ('full', 'Full'), ('heart', 'Heart-shaped'), ('round', 'Round'), ('bow', 'Cupid\'s Bow'), ('other', 'Other')
    ]
    lip_shape = models.CharField(max_length=20, choices=LIP_SHAPES, default='full')
    EYEBROW_PATTERNS = [
        ('arched', 'Arched'), ('straight', 'Straight'), ('curved', 'Curved'), ('thick', 'Thick'), ('thin', 'Thin'), ('other', 'Other')
    ]
    eyebrow_pattern = models.CharField(max_length=20, choices=EYEBROW_PATTERNS, default='straight')
    
    # Facial hair
    beard_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown', blank=True, null=True)
    BEARD_LENGTHS = [
        ('none', 'None'), ('stubble', 'Stubble'), ('short', 'Short'), ('medium', 'Medium'), ('long', 'Long'), ('other', 'Other')
    ]
    beard_length = models.CharField(max_length=10, choices=BEARD_LENGTHS, default='none', blank=True, null=True)
    mustache_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown', blank=True, null=True)
    mustache_length = models.CharField(max_length=10, choices=BEARD_LENGTHS, default='none', blank=True, null=True)
    
    # Distinctive marks
    FACIAL_MARKS = [
        ('none', 'None'), ('mole', 'Mole'), ('scar', 'Scar'), ('birthmark', 'Birthmark'), ('freckles', 'Freckles'), ('other', 'Other')
    ]
    distinctive_facial_marks = models.CharField(max_length=20, choices=FACIAL_MARKS, default='none', blank=True, null=True)
    BODY_MARKS = [
        ('none', 'None'), ('tattoo', 'Tattoo'), ('scar', 'Scar'), ('birthmark', 'Birthmark'), ('other', 'Other')
    ]
    distinctive_body_marks = models.CharField(max_length=20, choices=BODY_MARKS, default='none', blank=True, null=True)
    
    # Voice characteristics
    VOICE_TYPES = [
        ('normal', 'Normal'), ('thin', 'Thin'), ('rough', 'Rough'), ('deep', 'Deep'), ('soft', 'Soft'), ('nasal', 'Nasal'), ('other', 'Other')
    ]
    voice_type = models.CharField(max_length=20, choices=VOICE_TYPES, default='normal')
    
    # Body characteristics
    SKIN_TONES = [('fair', 'Fair'), ('light', 'Light'), ('medium', 'Medium'), 
                  ('olive', 'Olive'), ('brown', 'Brown'), ('dark', 'Dark')]
    skin_tone = models.CharField(max_length=20, choices=SKIN_TONES, default='fair')
    BODY_TYPES = [('athletic', 'Athletic'), ('slim', 'Slim'), ('muscular', 'Muscular'), 
                  ('average', 'Average'), ('plus_size', 'Plus Size'), ('other', 'Other')]
    body_type = models.CharField(max_length=20, choices=BODY_TYPES, default='athletic')
    
    # Fitness and risk levels (existing HybridWorker specific fields)
    FITNESS_LEVELS = [('beginner', 'Beginner'), ('intermediate', 'Intermediate'), 
                      ('advanced', 'Advanced'), ('elite', 'Elite Athlete')]
    fitness_level = models.CharField(max_length=20, choices=FITNESS_LEVELS, default='beginner')
    RISK_LEVELS = [('low', 'Low Risk Only'), ('moderate', 'Moderate Risk'),
                   ('high', 'High Risk'), ('extreme', 'Extreme Stunts')]
    risk_levels = models.CharField(max_length=20, choices=RISK_LEVELS, default='low')
    
    # Availability and other fields
    AVAILABILITY_CHOICES = [
        ('full_time', 'Full Time'), ('part_time', 'Part Time'),
        ('evenings', 'Evenings Only'), ('weekends', 'Weekends Only')
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='full_time')
    willing_to_relocate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    face_picture = models.ImageField(upload_to='profile_pictures/face/', null=True, blank=True)
    mid_range_picture = models.ImageField(upload_to='profile_pictures/mid/', null=True, blank=True)
    full_body_picture = models.ImageField(upload_to='profile_pictures/full/', null=True, blank=True)
    
    def has_bands_subscription(self):
        """Check if the band creator has an active bands subscription"""
        from payments.models import Subscription
        return Subscription.objects.filter(
            user=self.creator.user,
            plan__name='bands',
            is_active=True,
            status='active'
        ).exists()
    
    def get_profile_score(self):
        score_breakdown = {
            'total': 0,
            'profile_completion': 0,
            'media_content': 0,
            'member_count': 0,
            'band_details': 0,
            'details': {}
        }
        # Profile completion: Up to 30 points based on % of fields completed
        profile_fields = [
            bool(self.name), bool(self.description), bool(self.band_type), 
            bool(self.profile_picture), bool(self.contact_email or self.contact_phone), 
            bool(self.location)
        ]
        completed_fields = sum(1 for f in profile_fields if f)
        profile_percent = (completed_fields / len(profile_fields)) * 100
        if profile_percent == 100:
            score_breakdown['profile_completion'] = 30
            score_breakdown['details']['profile_completion'] = 'Complete band profile: +30 points'
        elif profile_percent >= 75:
            score_breakdown['profile_completion'] = 20
            score_breakdown['details']['profile_completion'] = 'Mostly complete band profile: +20 points'
        elif profile_percent >= 50:
            score_breakdown['profile_completion'] = 10
            score_breakdown['details']['profile_completion'] = 'Partially complete band profile: +10 points'
        else:
            score_breakdown['details']['profile_completion'] = 'Minimal band profile: +0 points (complete your band profile for up to +30 points)'
        # Media content: Up to 30 points based on quantity
        media_count = self.media.count()
        if media_count >= 6:
            score_breakdown['media_content'] = 30
            score_breakdown['details']['media_content'] = 'Maximum media (6 items): +30 points'
        elif media_count >= 4:
            score_breakdown['media_content'] = 20
            score_breakdown['details']['media_content'] = 'Good media (4-5 items): +20 points'
        elif media_count >= 2:
            score_breakdown['media_content'] = 10
            score_breakdown['details']['media_content'] = 'Basic media (2-3 items): +10 points'
        elif media_count == 1:
            score_breakdown['media_content'] = 5
            score_breakdown['details']['media_content'] = 'Minimal media (1 item): +5 points'
        else:
            score_breakdown['details']['media_content'] = 'No media: +0 points (add media for up to +30 points)'
        # Member count: Up to 30 points based on number of members
        member_count = self.member_count
        if member_count >= 10:
            score_breakdown['member_count'] = 30
            score_breakdown['details']['member_count'] = 'Large band (10+ members): +30 points'
        elif member_count >= 5:
            score_breakdown['member_count'] = 20
            score_breakdown['details']['member_count'] = 'Medium band (5-9 members): +20 points'
        elif member_count >= 3:
            score_breakdown['member_count'] = 10
            score_breakdown['details']['member_count'] = 'Small band (3-4 members): +10 points'
        elif member_count > 0:
            score_breakdown['member_count'] = 5
            score_breakdown['details']['member_count'] = 'Minimal band (1-2 members): +5 points'
        else:
            score_breakdown['details']['member_count'] = 'No members: +0 points (add members for up to +30 points)'
        # Band details: Up to 10 points for member positions
        members_with_positions = BandMembership.objects.filter(band=self, position__isnull=False).exclude(position='').count()
        if members_with_positions == member_count and member_count > 0:
            score_breakdown['band_details'] = 10
            score_breakdown['details']['band_details'] = 'All members have positions: +10 points'
        elif members_with_positions > 0:
            score_breakdown['band_details'] = 5
            score_breakdown['details']['band_details'] = 'Some members have positions: +5 points'
        else:
            score_breakdown['details']['band_details'] = 'No member positions: +0 points (add positions for up to +10 points)'
        # Calculate total
        score_breakdown['total'] = (
            score_breakdown['profile_completion'] +
            score_breakdown['media_content'] +
            score_breakdown['member_count'] +
            score_breakdown['band_details']
        )
        score_breakdown['total'] = min(score_breakdown['total'], 100)
        # Improvement tips
        if score_breakdown['total'] < 80:
            score_breakdown['improvement_tips'] = []
            if profile_percent < 100:
                score_breakdown['improvement_tips'].append('Complete your band profile for up to +30 points')
            if media_count < 6:
                score_breakdown['improvement_tips'].append('Add more media for up to +30 points')
            if member_count < 5:
                score_breakdown['improvement_tips'].append('Add more members for up to +30 points')
            if members_with_positions < member_count:
                score_breakdown['improvement_tips'].append('Add positions for all members for up to +10 points')
        return score_breakdown

