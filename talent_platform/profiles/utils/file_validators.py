from django.core.exceptions import ValidationError
from django.conf import settings

def validate_video_file(file):
    """
    Validate video file size and type.
    """
    # Check file size
    max_size = getattr(settings, 'MAX_VIDEO_SIZE', 100 * 1024 * 1024)  # 100 MB default
    if file.size > max_size:
        raise ValidationError(
            f"Video file size cannot exceed {max_size // (1024 * 1024)} MB. "
            f"Current size: {file.size // (1024 * 1024)} MB"
        )
    
    # Check file type
    allowed_types = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/quicktime', 'video/mkv']
    if hasattr(file, 'content_type') and file.content_type not in allowed_types:
        raise ValidationError(
            f"Invalid video format. Allowed formats: MP4, AVI, MOV, WMV, MKV. "
            f"Received: {file.content_type}"
        )
    
    return True

def validate_image_file(file):
    """
    Validate image file size and type.
    """
    # Check file size
    max_size = getattr(settings, 'MAX_IMAGE_SIZE', 10 * 1024 * 1024)  # 10 MB default
    if file.size > max_size:
        raise ValidationError(
            f"Image file size cannot exceed {max_size // (1024 * 1024)} MB. "
            f"Current size: {file.size // (1024 * 1024)} MB"
        )
    
    # Check file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if hasattr(file, 'content_type') and file.content_type not in allowed_types:
        raise ValidationError(
            f"Invalid image format. Allowed formats: JPEG, PNG, GIF, WebP. "
            f"Received: {file.content_type}"
        )
    
    return True

def get_file_size_mb(file):
    """
    Get file size in MB.
    """
    return round(file.size / (1024 * 1024), 2)

def get_max_file_sizes():
    """
    Get maximum file sizes for frontend validation.
    """
    return {
        'video_max_mb': getattr(settings, 'MAX_VIDEO_SIZE', 100 * 1024 * 1024) // (1024 * 1024),
        'image_max_mb': getattr(settings, 'MAX_IMAGE_SIZE', 10 * 1024 * 1024) // (1024 * 1024),
    } 