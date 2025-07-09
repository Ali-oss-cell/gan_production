from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Custom storage backend for media files using DigitalOcean Spaces (S3-compatible).
    This will store all media files in the specified bucket with the given location prefix.
    """
    location = 'media'  # Folder within the bucket where files will be stored
    file_overwrite = False  # Don't overwrite files with the same name
    default_acl = 'public-read'  # Make files publicly accessible by default
    
    # Use custom domain if configured
    custom_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
    
    # Specific configuration for video files
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        # Set appropriate content type and caching for video files
        if name.lower().endswith(('.mp4', '.mov', '.avi', '.wmv')):
            params['ContentType'] = 'video/mp4'
            params['CacheControl'] = 'max-age=86400'  # Cache for 24 hours
        return params
    
    def url(self, name):
        """
        Override url method to ensure proper URL generation with custom domain
        """
        if self.custom_domain:
            # Use custom domain with proper path structure
            return f"https://{self.custom_domain}/{self.location}/{name}"
        else:
            # Fall back to default S3 URL generation
            return super().url(name)


class S3MediaStorage(S3Boto3Storage):
    """
    Custom storage backend for media files using AWS S3.
    This will store all media files in the specified S3 bucket with the given location prefix.
    """
    location = 'media'  # Folder within the bucket where files will be stored
    file_overwrite = False  # Don't overwrite files with the same name
    default_acl = 'public-read'  # Make files publicly accessible by default
    custom_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
    
    # Specific configuration for video files
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        # Set appropriate content type and caching for video files
        if name.lower().endswith(('.mp4', '.mov', '.avi', '.wmv')):
            params['ContentType'] = 'video/mp4'
            params['CacheControl'] = 'max-age=86400'  # Cache for 24 hours
        return params