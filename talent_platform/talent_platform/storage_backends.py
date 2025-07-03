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
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') else None
    
    # Specific configuration for video files
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        # Set appropriate content type and caching for video files
        if name.lower().endswith(('.mp4', '.mov', '.avi', '.wmv')):
            params['ContentType'] = 'video/mp4'
            params['CacheControl'] = 'max-age=86400'  # Cache for 24 hours
        return params


class S3MediaStorage(S3Boto3Storage):
    """
    Custom storage backend for media files using AWS S3.
    This will store all media files in the specified S3 bucket with the given location prefix.
    """
    location = 'media'  # Folder within the bucket where files will be stored
    file_overwrite = False  # Don't overwrite files with the same name
    default_acl = 'public-read'  # Make files publicly accessible by default
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') else None
    
    # Specific configuration for video files
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        # Set appropriate content type and caching for video files
        if name.lower().endswith(('.mp4', '.mov', '.avi', '.wmv')):
            params['ContentType'] = 'video/mp4'
            params['CacheControl'] = 'max-age=86400'  # Cache for 24 hours
        return params