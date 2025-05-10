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
            image_count = self.media.filter(media_type='image').count()
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
            video_count = self.media.filter(media_type='video').count()
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
    country = models.CharField(max_length=25, null=False,default='country')
    date_of_birth = models.DateField(verbose_name="Date of Birth", blank=True, null=True, help_text="The user's date of birth.")

    def save(self, *args, **kwargs):
        # Process media file before saving
        if self.media_file and not self.pk:  # Only process new uploads
            try:
                # Process the media file
                processed_path = MediaProcessor.process_media(self.media_file)
                
                if processed_path:
                    # Save the processed file
                    with open(processed_path, 'rb') as f:
                        self.media_file.save(
                            os.path.basename(self.media_file.name),
                            ContentFile(f.read()),
                            save=False
                        )
                    
                    # Generate thumbnail for videos
                    if self.media_type == 'video':
                        thumbnail_path = self._generate_video_thumbnail(processed_path)
                        if thumbnail_path:
                            with open(thumbnail_path, 'rb') as f:
                                self.thumbnail.save(
                                    f"{os.path.splitext(self.media_file.name)[0]}_thumb.jpg",
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
        Generate a thumbnail from a video file.
        """
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
                    
                if image_count >= 3:
                    raise ValidationError("A band can have a maximum of 3 images.")
            
            elif self.media_type == 'video':
                if video_count is None:
                    video_count = self.band.media.filter(media_type='video').count()
                    self.band._band_video_count = video_count
                    
                if video_count >= 3:
                    raise ValidationError("A band can have a maximum of 3 videos.")
    
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
    
    # Core Classification - All Structured Fields
    PRIMARY_CATEGORIES = [
        ('photographer', 'Photographer'), ('cinematographer', 'Cinematographer'),
        ('director', 'Director'), ('editor', 'Video/Film Editor'),
        ('animator', 'Animator'), ('graphic_designer', 'Graphic Designer'),
        ('makeup_artist', 'Makeup Artist'), ('costume_designer', 'Costume Designer'),
        ('set_designer', 'Set Designer'), ('lighting_designer', 'Lighting Designer'),
        ('visual_artist', 'Visual Artist'), ('composer', 'Music Composer'),
        ('sound_designer', 'Sound Designer'), ('other', 'Other Visual Creator')
    ]
    primary_category = models.CharField(max_length=50, choices=PRIMARY_CATEGORIES)
    
    # Experience - Structured Numeric Fields
    years_experience = models.PositiveIntegerField()
    
    # Professional Level
    EXPERIENCE_LEVEL = [
        ('beginner', 'Beginner'), ('intermediate', 'Intermediate'),
        ('professional', 'Professional'), ('expert', 'Expert')
    ]
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL)
    
    # Portfolio - Simple URL, not text
    portfolio_link = models.URLField()
    
    # Many-to-Many Relationships for Searchable Categories
    tools = models.ManyToManyField('CreativeTool')  # Software, equipment, etc.
    styles = models.ManyToManyField('VisualStyle')  # Art/design styles
    industry_sectors = models.ManyToManyField('IndustrySector')  # Film, TV, etc.
    
    # Boolean Flags for Quick Filtering
    has_awards = models.BooleanField(default=False)
    has_professional_training = models.BooleanField(default=False)
    available_for_travel = models.BooleanField(default=False)
    available_for_remote_work = models.BooleanField(default=True)
    
    # Working Preferences - Structured Fields
    AVAILABILITY_CHOICES = [
        ('full_time', 'Full Time'), ('part_time', 'Part Time'),
        ('weekends', 'Weekends Only'), ('flexible', 'Flexible')
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES)
    
    # Price Range - Structured Field for Filtering
    RATE_RANGES = [
        ('low', 'Budget Friendly'), ('mid', 'Mid-Range'),
        ('high', 'Premium'), ('negotiable', 'Negotiable')
    ]
    rate_range = models.CharField(max_length=20, choices=RATE_RANGES)
    
    # Location Information
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    willing_to_relocate = models.BooleanField(default=False)
    
    # Languages - Structured Field
    languages = models.ManyToManyField('Language', through='VisualWorkerLanguage')
    
    # Structured Fields for Specialized Information
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ExpressiveWorker(models.Model):
    profile = models.OneToOneField(
        TalentUserProfile,
        on_delete=models.CASCADE,
        related_name='expressive_worker'
    )
    
    # Core Classification
    PERFORMER_TYPES = [
        ('actor', 'Actor'), ('voice_actor', 'Voice Actor'),
        ('singer', 'Singer'), ('dancer', 'Dancer'),
        ('musician', 'Musician'), ('comedian', 'Comedian'),
        ('host', 'TV/Event Host'), ('narrator', 'Narrator'),
        ('puppeteer', 'Puppeteer'), ('other', 'Other Performer')
    ]
    performer_type = models.CharField(max_length=50, choices=PERFORMER_TYPES)
    
    # Experience - Structured Fields
    years_experience = models.PositiveIntegerField()
    
    # Physical Attributes - All Numeric/Structured Fields
    height = models.FloatField(help_text="Height in cm")
    weight = models.FloatField(help_text="Weight in kg")
    
    # Age Range - Searchable Range
    age_min = models.PositiveIntegerField(help_text="Minimum age you can play")
    age_max = models.PositiveIntegerField(help_text="Maximum age you can play")
    
    # Appearance - Structured Choices
    HAIR_COLORS = [('blonde', 'Blonde'), ('brown', 'Brown'), ('black', 'Black'), 
                   ('red', 'Red'), ('gray', 'Gray/Silver'), ('other', 'Other')]
    hair_color = models.CharField(max_length=20, choices=HAIR_COLORS)
    
    EYE_COLORS = [('blue', 'Blue'), ('green', 'Green'), ('brown', 'Brown'), 
                  ('hazel', 'Hazel'), ('black', 'Black'), ('other', 'Other')]
    eye_color = models.CharField(max_length=20, choices=EYE_COLORS)
    
    BODY_TYPES = [('athletic', 'Athletic'), ('slim', 'Slim'), ('muscular', 'Muscular'), 
                  ('average', 'Average'), ('plus_size', 'Plus Size'), ('other', 'Other')]
    body_type = models.CharField(max_length=20, choices=BODY_TYPES)
    
    # Many-to-Many Relationships for Filtering
    performance_skills = models.ManyToManyField('PerformanceSkill')
    genres = models.ManyToManyField('PerformanceGenre')
    accents = models.ManyToManyField('Accent')
    languages = models.ManyToManyField('Language', through='PerformerLanguage')
    
    # Union Membership - Searchable Fields
    UNION_STATUS = [
        ('union', 'Union Member'), ('non_union', 'Non-Union'),
        ('eligible', 'Union Eligible'), ('fi_core', 'Fi-Core')
    ]
    union_status = models.CharField(max_length=20, choices=UNION_STATUS, blank=True, null=True)
    
    # Media Links - URLs, not text
    showreel_link = models.URLField(blank=True, null=True)
    
    # Boolean Filters
    available_for_auditions = models.BooleanField(default=True)
    willing_to_travel = models.BooleanField(default=True)
    has_passport = models.BooleanField(default=False)
    has_driving_license = models.BooleanField(default=False)
    comfortable_with_stunts = models.BooleanField(default=False)
    
    # Geographic Information
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    
    # Availability
    AVAILABILITY_CHOICES = [
        ('full_time', 'Full Time'), ('part_time', 'Part Time'),
        ('evenings', 'Evenings Only'), ('weekends', 'Weekends Only')
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update profile completion status after saving
        self.profile.update_profile_completion()
        
    def delete(self, *args, **kwargs):
        profile = self.profile
        super().delete(*args, **kwargs)
        # Update profile completion status after deletion
        profile.update_profile_completion()

class HybridWorker(models.Model):
    profile = models.OneToOneField(TalentUserProfile, on_delete=models.CASCADE, related_name='hybrid_worker')
    
    # Core Classification
    HYBRID_TYPES = [
        ('model', 'Fashion/Commercial Model'), ('stunt_performer', 'Stunt Performer'),
        ('body_double', 'Body Double'), ('motion_capture', 'Motion Capture Artist'),
        ('background_actor', 'Background Actor'), ('specialty_performer', 'Specialty Performer'),
        ('other', 'Other Physical Performer')
    ]
    hybrid_type = models.CharField(max_length=50, choices=HYBRID_TYPES)
    
    # Experience - Structured Fields
    years_experience = models.PositiveIntegerField()
    
    # Physical Attributes - All Numeric/Structured Fields
    height = models.FloatField(help_text="Height in cm")
    weight = models.FloatField(help_text="Weight in kg")
    
    # Measurements - Structured Numeric Fields
    chest = models.FloatField(blank=True, null=True)
    waist = models.FloatField(blank=True, null=True)
    hips = models.FloatField(blank=True, null=True)
    
    # Physical Attributes - Structured Choices
    HAIR_COLORS = [('blonde', 'Blonde'), ('brown', 'Brown'), ('black', 'Black'), 
                   ('red', 'Red'), ('gray', 'Gray/Silver'), ('other', 'Other')]
    hair_color = models.CharField(max_length=20, choices=HAIR_COLORS)
    
    EYE_COLORS = [('blue', 'Blue'), ('green', 'Green'), ('brown', 'Brown'), 
                  ('hazel', 'Hazel'), ('black', 'Black'), ('other', 'Other')]
    eye_color = models.CharField(max_length=20, choices=EYE_COLORS)
    
    SKIN_TONES = [('fair', 'Fair'), ('light', 'Light'), ('medium', 'Medium'), 
                  ('olive', 'Olive'), ('brown', 'Brown'), ('dark', 'Dark')]
    skin_tone = models.CharField(max_length=20, choices=SKIN_TONES)
    
    BODY_TYPES = [('athletic', 'Athletic'), ('slim', 'Slim'), ('muscular', 'Muscular'), 
                  ('average', 'Average'), ('plus_size', 'Plus Size'), ('other', 'Other')]
    body_type = models.CharField(max_length=20, choices=BODY_TYPES)
    
    # Physical Abilities - Many-to-Many for Filtering
    physical_skills = models.ManyToManyField('PhysicalSkill')
    stunt_specialties = models.ManyToManyField('StuntSpecialty', blank=True)
    dance_styles = models.ManyToManyField('DanceStyle', blank=True)
    sports = models.ManyToManyField('Sport', blank=True)
    
    # Training & Certification - Structured Fields
    FITNESS_LEVELS = [('beginner', 'Beginner'), ('intermediate', 'Intermediate'), 
                      ('advanced', 'Advanced'), ('elite', 'Elite Athlete')]
    fitness_level = models.CharField(max_length=20, choices=FITNESS_LEVELS)
    
    # Boolean Filters for Quick Searches
    has_stunt_insurance = models.BooleanField(default=False)
    has_tattoos = models.BooleanField(default=False)
    has_piercings = models.BooleanField(default=False)
    has_unique_features = models.BooleanField(default=False)
    
    # Safety & Risk
    RISK_LEVELS = [('low', 'Low Risk Only'), ('moderate', 'Moderate Risk'),
                   ('high', 'High Risk'), ('extreme', 'Extreme Stunts')]
    risk_comfort = models.CharField(max_length=20, choices=RISK_LEVELS)
    
    # Training & Certifications
    has_formal_training = models.BooleanField(default=False)
    certified_skills = models.ManyToManyField('CertifiedSkill', blank=True)
    
    # Languages
    languages = models.ManyToManyField('Language', through='HybridWorkerLanguage')
    
    # Geographic Information
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    willing_to_relocate = models.BooleanField(default=False)
    
    # Media - Simple URL Fields
    portfolio_link = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

