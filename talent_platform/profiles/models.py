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
    is_verified = models.BooleanField(default=False, db_index=True)
    profile_complete = models.BooleanField(default=False, db_index=True)  # Track profile completion status
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    aboutyou = models.TextField(blank=True, null=True)

    ACCOUNT_TYPES = [
        ('platinum', 'Platinum'),
        ('premium', 'Premium'),
        ('free', 'Free'),
    ]
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='free', db_index=True)
    
    # Basic profile fields that were missing
    country = models.CharField(max_length=25, blank=True, default='', db_index=True)
    city = models.CharField(max_length=25, blank=True, default='', db_index=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    date_of_birth = models.DateField(verbose_name="Date of Birth", blank=True, null=True, help_text="The user's date of birth.", db_index=True)
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male', db_index=True)
    
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
            'social_media': 0,
            'details': {}
        }
        
        # Account tier - More balanced scoring
        if self.account_type == 'platinum':
            score_breakdown['account_tier'] = 25
            score_breakdown['details']['account_tier'] = 'Platinum account: +25 points'
        elif self.account_type == 'premium':
            score_breakdown['account_tier'] = 15
            score_breakdown['details']['account_tier'] = 'Premium account: +15 points'
        else:
            score_breakdown['account_tier'] = 5
            score_breakdown['details']['account_tier'] = 'Free account: +5 points'
        
        # Verification - Increased importance
        if self.is_verified:
            score_breakdown['verification'] = 25
            score_breakdown['details']['verification'] = 'Verified profile: +25 points'
        else:
            score_breakdown['details']['verification'] = 'Not verified: +0 points (get verified for +25 points)'
        
        # Profile completion - More detailed scoring
        completion_score = 0
        completion_details = []
        
        # Basic profile fields
        if self.aboutyou and len(self.aboutyou.strip()) > 50:
            completion_score += 5
            completion_details.append('About section: +5 points')
        if self.profile_picture:
            completion_score += 5
            completion_details.append('Profile picture: +5 points')
        if self.country and self.country != 'country':
            completion_score += 3
            completion_details.append('Country specified: +3 points')
        if self.date_of_birth:
            completion_score += 2
            completion_details.append('Date of birth: +2 points')
        
        # Specialization completion
        has_specialization = self.has_specialization()
        if has_specialization:
            completion_score += 10
            completion_details.append('Specialization added: +10 points')
        
        score_breakdown['profile_completion'] = completion_score
        if completion_details:
            score_breakdown['details']['profile_completion'] = '; '.join(completion_details)
        else:
            score_breakdown['details']['profile_completion'] = 'Profile incomplete: +0 points (complete your profile for up to +25 points)'
        
        # Media content - More granular scoring
        media_count = self.media.filter(is_test_video=False).count()
        if media_count >= 6:
            score_breakdown['media_content'] = 20
            score_breakdown['details']['media_content'] = 'Excellent portfolio (6+ items): +20 points'
        elif media_count >= 4:
            score_breakdown['media_content'] = 15
            score_breakdown['details']['media_content'] = 'Strong portfolio (4-5 items): +15 points'
        elif media_count >= 2:
            score_breakdown['media_content'] = 10
            score_breakdown['details']['media_content'] = 'Good portfolio (2-3 items): +10 points'
        elif media_count >= 1:
            score_breakdown['media_content'] = 5
            score_breakdown['details']['media_content'] = 'Basic portfolio (1 item): +5 points'
        else:
            score_breakdown['media_content'] = 0
            score_breakdown['details']['media_content'] = 'No portfolio items: +0 points (add portfolio items for up to +20 points)'
        
        # Specialization - More detailed scoring
        specialization_score = 0
        specialization_details = []
        
        if has_specialization:
            # Count specializations
            spec_count = 0
            if hasattr(self, 'visual_worker'):
                spec_count += 1
                specialization_details.append('Visual Worker')
            if hasattr(self, 'expressive_worker'):
                spec_count += 1
                specialization_details.append('Expressive Worker')
            if hasattr(self, 'hybrid_worker'):
                spec_count += 1
                specialization_details.append('Hybrid Worker')
            
            # Base points for having specialization
            specialization_score = 10
            # Bonus for multiple specializations
            if spec_count > 1:
                specialization_score += 5
                specialization_details.append(f'Multi-specialization bonus: +5 points')
            
            score_breakdown['specialization'] = specialization_score
            score_breakdown['details']['specialization'] = f'Specializations: {", ".join(specialization_details)} (+{specialization_score} points)'
        else:
            score_breakdown['specialization'] = 0
            score_breakdown['details']['specialization'] = 'No specialization: +0 points (add a specialization for +10 points)'
        
        # Social media presence - New scoring category
        social_media_score = 0
        social_details = []
        
        if hasattr(self, 'social_media_links'):
            social_links = self.social_media_links
            link_count = sum([
                bool(social_links.facebook),
                bool(social_links.twitter),
                bool(social_links.instagram),
                bool(social_links.linkedin),
                bool(social_links.youtube),
                bool(social_links.tiktok),
                bool(social_links.snapchat)
            ])
            
            if link_count >= 4:
                social_media_score = 10
                social_details.append('Strong social presence (4+ links): +10 points')
            elif link_count >= 2:
                social_media_score = 5
                social_details.append('Good social presence (2-3 links): +5 points')
            elif link_count >= 1:
                social_media_score = 2
                social_details.append('Basic social presence (1 link): +2 points')
        
        score_breakdown['social_media'] = social_media_score
        if social_details:
            score_breakdown['details']['social_media'] = '; '.join(social_details)
        else:
            score_breakdown['details']['social_media'] = 'No social media links: +0 points (add social links for up to +10 points)'
        
        # Calculate total
        score_breakdown['total'] = (
            score_breakdown['account_tier'] +
            score_breakdown['verification'] +
            score_breakdown['profile_completion'] +
            score_breakdown['media_content'] +
            score_breakdown['specialization'] +
            score_breakdown['social_media']
        )
        score_breakdown['total'] = min(score_breakdown['total'], 100)
        
        # Improved improvement tips
        if score_breakdown['total'] < 70:
            score_breakdown['improvement_tips'] = []
            if self.account_type == 'free':
                score_breakdown['improvement_tips'].append('Upgrade to Premium (+10) or Platinum (+20) for more points')
            if not self.is_verified:
                score_breakdown['improvement_tips'].append('Verify your profile for +25 points')
            if completion_score < 15:
                score_breakdown['improvement_tips'].append('Complete your profile details for up to +25 points')
            if media_count < 4:
                score_breakdown['improvement_tips'].append('Add more portfolio items for up to +20 points')
            if not has_specialization:
                score_breakdown['improvement_tips'].append('Add a specialization for +10 points')
            if social_media_score < 5:
                score_breakdown['improvement_tips'].append('Add social media links for up to +10 points')
        
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
            'free': 1,        # Changed from 2 to 1 - Very limited for free users
            'premium': 4,
            'platinum': 6
        }
        return limits.get(self.account_type, 0)
        
    def get_video_limit(self):
        """
        Get the maximum number of videos allowed based on account type.
        """
        limits = {
            'free': 0,        # Changed from 1 to 0 - No videos for free users
            'premium': 2,
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




    def can_use_advanced_search(self):
        """
        Check if user can use advanced search filters.
        """
        return self.account_type in ['premium', 'platinum']

    def can_get_priority_support(self):
        """
        Check if user gets priority support.
        """
        return self.account_type in ['premium', 'platinum']

    def get_search_boost(self):
        """
        Get search ranking boost multiplier.
        """
        boosts = {
            'free': 0.1,          # Very low visibility
            'premium': 0.5,       # Medium visibility  
            'platinum': 1.0        # High visibility
        }
        return boosts.get(self.account_type, 0.1)

    def can_create_custom_url(self):
        """
        Check if user can create custom profile URL.
        """
        return self.account_type == 'platinum'

    def can_get_featured_placement(self):
        """
        Check if user can get featured profile placement.
        """
        return self.account_type == 'platinum'

    def get_upgrade_benefits(self):
        """
        Get benefits that would be unlocked with upgrade.
        """
        if self.account_type == 'free':
            return {
                'media': {
                    'current': f"{self.get_image_limit()} image(s), {self.get_video_limit()} video(s)",
                    'premium': "4 images, 2 videos",
                    'platinum': "6 images, 4 videos"
                },
                'features': {
                    'current': "Basic profile only",
                    'premium': "Verification badge, Enhanced search visibility",
                    'platinum': "All Premium features + Featured placement, Custom URL"
                },
                'visibility': {
                    'current': "Low search visibility (10% boost)",
                    'premium': "Enhanced visibility (50% boost)",
                    'platinum': "Highest visibility (100% boost) + Featured placement"
                }
            }
        elif self.account_type == 'premium':
            return {
                'platinum_upgrade': {
                    'additional_media': "2 more images, 2 more videos",
                    'additional_features': "Featured placement, Custom URL",
                    'features': "Featured placement, Custom URL",
                    'visibility': "Highest visibility + Featured placement"
                }
            }
        return {}


    country = models.CharField(max_length=25, null=False, default='country', db_index=True)
    city = models.CharField(max_length=25, null=False, default='city', db_index=True)
    phone = models.CharField(max_length=20, null=False, default="")
    date_of_birth = models.DateField(verbose_name="Date of Birth", blank=True, null=True, help_text="The user's date of birth.", db_index=True)
    #parental_approval = models.BooleanField(default=False, verbose_name="Parental Approval", help_text="Indicates whether parental approval has been provided for minors.")

    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Male", db_index=True)

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

    class Meta:
        indexes = [
            models.Index(fields=['account_type', 'is_verified']),
            models.Index(fields=['country', 'city']),
            models.Index(fields=['gender', 'date_of_birth']),
            models.Index(fields=['profile_complete', 'account_type']),
        ]

class BackGroundJobsProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='background_profile'
    )
    profile_picture = models.ImageField(upload_to='background_profile_pictures/', blank=True, null=True)
    country = models.CharField(max_length=25, null=False, default='country', db_index=True)
    date_of_birth = models.DateField(verbose_name="Date of Birth", blank=True, null=True, db_index=True)
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Male", db_index=True)
    
    ACCOUNT_TYPES = [
        ('back_ground_jobs', 'Background Jobs'),
        ('free', 'Free'),
    ]
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='free', db_index=True)

    def get_profile_score(self):
        score_breakdown = {
            'total': 0,
            'account_tier': 25,  # Reduced from 50 to 25 for more balanced scoring
            'profile_completion': 0,
            'item_diversity': 0,
            'item_quantity': 0,
            'details': {}
        }
        score_breakdown['details']['account_tier'] = 'All accounts paid: +25 points'
        # Profile completion: 15 points for filling basic fields (more comprehensive check)
        profile_complete = bool(
            self.country and 
            self.country != 'country' and  # Check it's not the default value
            self.date_of_birth and 
            self.gender and 
            self.gender != 'Male'  # Check it's not the default value
        )
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

    class Meta:
        indexes = [
            models.Index(fields=['account_type', 'gender']),
            models.Index(fields=['country', 'date_of_birth']),
        ]






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
    name = models.CharField(max_length=124, blank=False, null=False, default="Untitled Media", db_index=True)
    media_info = models.TextField(max_length=160, blank=False, null=False)
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, db_index=True)
    media_file = models.FileField(upload_to=user_media_path)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_of_birth = models.DateField(verbose_name="Date of Birth", blank=True, null=True, help_text="The user's date of birth.")
    # New fields for test video logic
    is_test_video = models.BooleanField(default=False, help_text="Is this a required test video for actor/comparse?", db_index=True)
    test_video_number = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Test video order (1-5)")
    # New: Special flag for the 1-minute 'about yourself' video
    is_about_yourself_video = models.BooleanField(default=False, help_text="Is this the 1-minute 'about yourself' video?", db_index=True)

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
            
        # Process media file before saving (only images, videos go directly to S3)
        if self.media_file and not self.pk:  # Only process new uploads
            try:
                # Only process images, videos go directly to S3
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
                    
            except Exception as e:
                print(f"Error processing media: {str(e)}")
        
        super().save(*args, **kwargs)
    
    def _generate_video_thumbnail(self, video_path):
        """
        Video thumbnail generation disabled - no FFmpeg available
        """
        print("Video thumbnail generation disabled - no FFmpeg available")
        return None

    def __str__(self):
        return f"{self.talent.user.email}'s {self.media_type} - {self.media_file.name}"
   

# Video processing signal handler removed - videos go directly to S3


    #socil media links
class SocialMediaLinks(models.Model):
    user = models.OneToOneField(TalentUserProfile, on_delete=models.CASCADE, related_name='social_media_links')
    facebook = models.URLField(blank=True, null=True, verbose_name="Facebook URL")
    instagram = models.URLField(blank=True, null=True, verbose_name="Instagram URL")
    youtube = models.URLField(blank=True, null=True, verbose_name="YouTube URL")
    tiktok = models.URLField(blank=True, null=True, verbose_name="TikTok URL")

    def get_user_links(self):
        """Return all social media links as a dictionary"""
        return {
            'facebook': self.facebook,
            'instagram': self.instagram,
            'youtube': self.youtube,
            'tiktok': self.tiktok,
        }

    def has_social_media_links(self):
        return any([self.facebook, self.instagram, self.youtube, self.tiktok])
        
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
        null=True, blank=True
    )
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, db_index=True)
    genre = models.ForeignKey(
        Genre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_items'  # Dynamically generates unique related_name
    )
    is_for_rent = models.BooleanField(default=False, db_index=True)
    is_for_sale = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='item_images/')

    class Meta:
        abstract = True  # This makes it an abstract base class
        indexes = [
            models.Index(fields=['name', 'price']),
            models.Index(fields=['is_for_rent', 'is_for_sale']),
            models.Index(fields=['created_at', 'price']),
        ]

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
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
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
    band_type = models.CharField(max_length=20, choices=BAND_TYPE_CHOICES, default='musical', db_index=True)
    
    # Band profile picture
    profile_picture = models.ImageField(upload_to='band_profile_pictures/', blank=True, null=True)
    
    # Band contact information
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Band location
    location = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    
    # Band website and social media
    website = models.URLField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['band_type', 'location']),
            models.Index(fields=['created_at', 'band_type']),
            models.Index(fields=['name', 'band_type']),
        ]

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
    primary_category = models.CharField(max_length=50, choices=PRIMARY_CATEGORIES, default='photographer', db_index=True)
    years_experience = models.PositiveIntegerField(default=0, db_index=True)
    EXPERIENCE_LEVEL = [
        ('beginner', 'Beginner'), ('intermediate', 'Intermediate'),
        ('professional', 'Professional'), ('expert', 'Expert')
    ]
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL, default='beginner', db_index=True)
    portfolio_link = models.URLField(blank=True, null=True)
    AVAILABILITY_CHOICES = [
        ('full_time', 'Full Time'), ('part_time', 'Part Time'),
        ('weekends', 'Weekends Only'), ('flexible', 'Flexible')
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='full_time', db_index=True)
    RATE_RANGES = [
        ('low', 'Budget Friendly'), ('mid', 'Mid-Range'),
        ('high', 'Premium'), ('negotiable', 'Negotiable')
    ]
    rate_range = models.CharField(max_length=20, choices=RATE_RANGES, default='low', db_index=True)
    willing_to_relocate = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    face_picture = models.ImageField(upload_to='profile_pictures/face/', null=True, blank=True)
    mid_range_picture = models.ImageField(upload_to='profile_pictures/mid/', null=True, blank=True)
    full_body_picture = models.ImageField(upload_to='profile_pictures/full/', null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['primary_category', 'experience_level']),
            models.Index(fields=['years_experience', 'availability']),
            models.Index(fields=['rate_range', 'willing_to_relocate']),
            models.Index(fields=['created_at', 'primary_category']),
        ]

class ExpressiveWorker(models.Model):
    profile = models.OneToOneField(TalentUserProfile, on_delete=models.CASCADE, related_name='expressive_worker')
    PERFORMER_TYPES = [
        ('actor', 'Actor'),('comparse','Comparse'),('voice_actor', 'Voice Actor'),
        ('singer', 'Singer'), ('dancer', 'Dancer'),
        ('musician', 'Musician'), ('comedian', 'Comedian'),
        ('host', 'TV/Event Host'), ('narrator', 'Narrator'),
        ('puppeteer', 'Puppeteer'), ('other', 'Other Performer')
    ]
    performer_type = models.CharField(max_length=50, choices=PERFORMER_TYPES, default='actor', db_index=True)
    years_experience = models.PositiveIntegerField(default=0, db_index=True)
    height = models.FloatField(default=0.0, help_text="Height in cm", db_index=True)
    weight = models.FloatField(default=0.0, help_text="Weight in kg", db_index=True)
    HAIR_COLORS = [('blonde', 'Blonde'), ('brown', 'Brown'), ('black', 'Black'), 
                   ('red', 'Red'), ('gray', 'Gray/Silver'), ('other', 'Other')]
    hair_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown', db_index=True)
    # New: Hair type
    HAIR_TYPES = [
        ('straight', 'Straight'), ('wavy', 'Wavy'), ('curly', 'Curly'), ('coily', 'Coily'), ('bald', 'Bald'), ('other', 'Other')
    ]
    hair_type = models.CharField(max_length=20, choices=HAIR_TYPES, default='straight', db_index=True)
    # New: Skin tone (reuse HybridWorker's choices)
    SKIN_TONES = [
        ('fair', 'Fair'), ('light', 'Light'), ('medium', 'Medium'), 
        ('olive', 'Olive'), ('brown', 'Brown'), ('dark', 'Dark')
    ]
    skin_tone = models.CharField(max_length=20, choices=SKIN_TONES, default='fair', db_index=True)
    EYE_COLORS = [('blue', 'Blue'), ('green', 'Green'), ('brown', 'Brown'), 
                  ('hazel', 'Hazel'), ('black', 'Black'), ('other', 'Other')]
    eye_color = models.CharField(max_length=20, choices=EYE_COLORS, default='brown', db_index=True)
    # New: Eye size
    EYE_SIZES = [
        ('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')
    ]
    eye_size = models.CharField(max_length=10, choices=EYE_SIZES, default='medium', db_index=True)
    # New: Eye pattern
    EYE_PATTERNS = [
        ('normal', 'Normal'), ('protruding', 'Protruding'), ('sunken', 'Sunken'), ('almond', 'Almond'), ('round', 'Round'), ('other', 'Other')
    ]
    eye_pattern = models.CharField(max_length=20, choices=EYE_PATTERNS, default='normal', db_index=True)
    # New: Face shape
    FACE_SHAPES = [
        ('oval', 'Oval'), ('round', 'Round'), ('square', 'Square'), ('heart', 'Heart'), ('diamond', 'Diamond'), ('long', 'Long'), ('other', 'Other')
    ]
    face_shape = models.CharField(max_length=20, choices=FACE_SHAPES, default='oval', db_index=True)
    # New: Forehead shape
    FOREHEAD_SHAPES = [
        ('broad', 'Broad'), ('narrow', 'Narrow'), ('rounded', 'Rounded'), ('straight', 'Straight'), ('other', 'Other')
    ]
    forehead_shape = models.CharField(max_length=20, choices=FOREHEAD_SHAPES, default='straight', db_index=True)
    # New: Lip shape
    LIP_SHAPES = [
        ('thin', 'Thin'), ('full', 'Full'), ('heart', 'Heart-shaped'), ('round', 'Round'), ('bow', 'Cupid\'s Bow'), ('other', 'Other')
    ]
    lip_shape = models.CharField(max_length=20, choices=LIP_SHAPES, default='full', db_index=True)
    # New: Eyebrow pattern
    EYEBROW_PATTERNS = [
        ('arched', 'Arched'), ('straight', 'Straight'), ('curved', 'Curved'), ('thick', 'Thick'), ('thin', 'Thin'), ('other', 'Other')
    ]
    eyebrow_pattern = models.CharField(max_length=20, choices=EYEBROW_PATTERNS, default='straight', db_index=True)
    # New: Beard color
    BEARD_COLORS = HAIR_COLORS
    beard_color = models.CharField(max_length=20, choices=BEARD_COLORS, default='brown', blank=True, null=True, db_index=True)
    # New: Beard length
    BEARD_LENGTHS = [
        ('none', 'None'), ('stubble', 'Stubble'), ('short', 'Short'), ('medium', 'Medium'), ('long', 'Long'), ('other', 'Other')
    ]
    beard_length = models.CharField(max_length=10, choices=BEARD_LENGTHS, default='none', blank=True, null=True, db_index=True)
    # New: Mustache color
    mustache_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown', blank=True, null=True, db_index=True)
    # New: Mustache length
    mustache_length = models.CharField(max_length=10, choices=BEARD_LENGTHS, default='none', blank=True, null=True, db_index=True)
    # New: Distinctive facial marks
    FACIAL_MARKS = [
        ('none', 'None'), ('mole', 'Mole'), ('scar', 'Scar'), ('birthmark', 'Birthmark'), ('freckles', 'Freckles'), ('other', 'Other')
    ]
    distinctive_facial_marks = models.CharField(max_length=20, choices=FACIAL_MARKS, default='none', blank=True, null=True, db_index=True)
    # New: Distinctive body marks
    BODY_MARKS = [
        ('none', 'None'), ('tattoo', 'Tattoo'), ('scar', 'Scar'), ('birthmark', 'Birthmark'), ('other', 'Other')
    ]
    distinctive_body_marks = models.CharField(max_length=20, choices=BODY_MARKS, default='none', blank=True, null=True, db_index=True)
    # New: Voice type
    VOICE_TYPES = [
        ('normal', 'Normal'), ('thin', 'Thin'), ('rough', 'Rough'), ('deep', 'Deep'), ('soft', 'Soft'), ('nasal', 'Nasal'), ('other', 'Other')
    ]
    voice_type = models.CharField(max_length=20, choices=VOICE_TYPES, default='normal', db_index=True)
    BODY_TYPES = [('athletic', 'Athletic'), ('slim', 'Slim'), ('muscular', 'Muscular'), 
                  ('average', 'Average'), ('plus_size', 'Plus Size'), ('other', 'Other')]
    body_type = models.CharField(max_length=20, choices=BODY_TYPES, default='average', db_index=True)
    AVAILABILITY_CHOICES = [
        ('full_time', 'Full Time'), ('part_time', 'Part Time'),
        ('evenings', 'Evenings Only'), ('weekends', 'Weekends Only')
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='full_time', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    face_picture = models.ImageField(upload_to='profile_pictures/face/', null=True, blank=True)
    mid_range_picture = models.ImageField(upload_to='profile_pictures/mid/', null=True, blank=True)
    full_body_picture = models.ImageField(upload_to='profile_pictures/full/', null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['performer_type', 'years_experience']),
            models.Index(fields=['hair_color', 'eye_color']),
            models.Index(fields=['height', 'weight']),
            models.Index(fields=['body_type', 'availability']),
            models.Index(fields=['created_at', 'performer_type']),
        ]

class HybridWorker(models.Model):
    profile = models.OneToOneField(TalentUserProfile, on_delete=models.CASCADE, related_name='hybrid_worker')
    HYBRID_TYPES = [
        ('model', 'Fashion/Commercial Model'), ('stunt_performer', 'Stunt Performer'),
        ('body_double', 'Body Double'), ('motion_capture', 'Motion Capture Artist'),
        ('background_actor', 'Background Actor'), ('specialty_performer', 'Specialty Performer'),
        ('other', 'Other Physical Performer'),
    ]
    hybrid_type = models.CharField(max_length=50, choices=HYBRID_TYPES, default='model', db_index=True)
    years_experience = models.PositiveIntegerField(default=0, db_index=True)
    height = models.FloatField(default=0.0, help_text="Height in cm", db_index=True)
    weight = models.FloatField(default=0.0, help_text="Weight in kg", db_index=True)
    
    # Hair characteristics
    HAIR_COLORS = [('blonde', 'Blonde'), ('brown', 'Brown'), ('black', 'Black'), 
                   ('red', 'Red'), ('gray', 'Gray/Silver'), ('other', 'Other')]
    hair_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown', db_index=True)
    HAIR_TYPES = [
        ('straight', 'Straight'), ('wavy', 'Wavy'), ('curly', 'Curly'), ('coily', 'Coily'), ('bald', 'Bald'), ('other', 'Other')
    ]
    hair_type = models.CharField(max_length=20, choices=HAIR_TYPES, default='straight', db_index=True)
    
    # Eye characteristics
    EYE_COLORS = [('blue', 'Blue'), ('green', 'Green'), ('brown', 'Brown'), 
                  ('hazel', 'Hazel'), ('black', 'Black'), ('other', 'Other')]
    eye_color = models.CharField(max_length=20, choices=EYE_COLORS, default='brown', db_index=True)
    EYE_SIZES = [
        ('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')
    ]
    eye_size = models.CharField(max_length=10, choices=EYE_SIZES, default='medium', db_index=True)
    EYE_PATTERNS = [
        ('normal', 'Normal'), ('protruding', 'Protruding'), ('sunken', 'Sunken'), ('almond', 'Almond'), ('round', 'Round'), ('other', 'Other')
    ]
    eye_pattern = models.CharField(max_length=20, choices=EYE_PATTERNS, default='normal', db_index=True)
    
    # Facial characteristics
    FACE_SHAPES = [
        ('oval', 'Oval'), ('round', 'Round'), ('square', 'Square'), ('heart', 'Heart'), ('diamond', 'Diamond'), ('long', 'Long'), ('other', 'Other')
    ]
    face_shape = models.CharField(max_length=20, choices=FACE_SHAPES, default='oval', db_index=True)
    FOREHEAD_SHAPES = [
        ('broad', 'Broad'), ('narrow', 'Narrow'), ('rounded', 'Rounded'), ('straight', 'Straight'), ('other', 'Other')
    ]
    forehead_shape = models.CharField(max_length=20, choices=FOREHEAD_SHAPES, default='straight', db_index=True)
    LIP_SHAPES = [
        ('thin', 'Thin'), ('full', 'Full'), ('heart', 'Heart-shaped'), ('round', 'Round'), ('bow', 'Cupid\'s Bow'), ('other', 'Other')
    ]
    lip_shape = models.CharField(max_length=20, choices=LIP_SHAPES, default='full', db_index=True)
    EYEBROW_PATTERNS = [
        ('arched', 'Arched'), ('straight', 'Straight'), ('curved', 'Curved'), ('thick', 'Thick'), ('thin', 'Thin'), ('other', 'Other')
    ]
    eyebrow_pattern = models.CharField(max_length=20, choices=EYEBROW_PATTERNS, default='straight', db_index=True)
    
    # Facial hair
    beard_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown', blank=True, null=True, db_index=True)
    BEARD_LENGTHS = [
        ('none', 'None'), ('stubble', 'Stubble'), ('short', 'Short'), ('medium', 'Medium'), ('long', 'Long'), ('other', 'Other')
    ]
    beard_length = models.CharField(max_length=10, choices=BEARD_LENGTHS, default='none', blank=True, null=True, db_index=True)
    mustache_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown', blank=True, null=True, db_index=True)
    mustache_length = models.CharField(max_length=10, choices=BEARD_LENGTHS, default='none', blank=True, null=True, db_index=True)
    
    # Distinctive marks
    FACIAL_MARKS = [
        ('none', 'None'), ('mole', 'Mole'), ('scar', 'Scar'), ('birthmark', 'Birthmark'), ('freckles', 'Freckles'), ('other', 'Other')
    ]
    distinctive_facial_marks = models.CharField(max_length=20, choices=FACIAL_MARKS, default='none', blank=True, null=True, db_index=True)
    BODY_MARKS = [
        ('none', 'None'), ('tattoo', 'Tattoo'), ('scar', 'Scar'), ('birthmark', 'Birthmark'), ('other', 'Other')
    ]
    distinctive_body_marks = models.CharField(max_length=20, choices=BODY_MARKS, default='none', blank=True, null=True, db_index=True)
    
    # Voice characteristics
    VOICE_TYPES = [
        ('normal', 'Normal'), ('thin', 'Thin'), ('rough', 'Rough'), ('deep', 'Deep'), ('soft', 'Soft'), ('nasal', 'Nasal'), ('other', 'Other')
    ]
    voice_type = models.CharField(max_length=20, choices=VOICE_TYPES, default='normal', db_index=True)
    
    # Body characteristics
    SKIN_TONES = [('fair', 'Fair'), ('light', 'Light'), ('medium', 'Medium'), 
                  ('olive', 'Olive'), ('brown', 'Brown'), ('dark', 'Dark')]
    skin_tone = models.CharField(max_length=20, choices=SKIN_TONES, default='fair', db_index=True)
    BODY_TYPES = [('athletic', 'Athletic'), ('slim', 'Slim'), ('muscular', 'Muscular'), 
                  ('average', 'Average'), ('plus_size', 'Plus Size'), ('other', 'Other')]
    body_type = models.CharField(max_length=20, choices=BODY_TYPES, default='athletic', db_index=True)
    
    # Fitness and risk levels (existing HybridWorker specific fields)
    FITNESS_LEVELS = [('beginner', 'Beginner'), ('intermediate', 'Intermediate'), 
                      ('advanced', 'Advanced'), ('elite', 'Elite Athlete')]
    fitness_level = models.CharField(max_length=20, choices=FITNESS_LEVELS, default='beginner', db_index=True)
    RISK_LEVELS = [('low', 'Low Risk Only'), ('moderate', 'Moderate Risk'),
                   ('high', 'High Risk'), ('extreme', 'Extreme Stunts')]
    risk_levels = models.CharField(max_length=20, choices=RISK_LEVELS, default='low', db_index=True)
    
    # Availability and other fields
    AVAILABILITY_CHOICES = [
        ('full_time', 'Full Time'), ('part_time', 'Part Time'),
        ('evenings', 'Evenings Only'), ('weekends', 'Weekends Only')
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='full_time', db_index=True)
    willing_to_relocate = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    face_picture = models.ImageField(upload_to='profile_pictures/face/', null=True, blank=True)
    mid_range_picture = models.ImageField(upload_to='profile_pictures/mid/', null=True, blank=True)
    full_body_picture = models.ImageField(upload_to='profile_pictures/full/', null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['hybrid_type', 'years_experience']),
            models.Index(fields=['hair_color', 'eye_color', 'skin_tone']),
            models.Index(fields=['height', 'weight']),
            models.Index(fields=['fitness_level', 'risk_levels']),
            models.Index(fields=['body_type', 'availability']),
            models.Index(fields=['created_at', 'hybrid_type']),
        ]

