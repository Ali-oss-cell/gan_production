import os
from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import tempfile

class MediaProcessor:
    MAX_IMAGE_SIZE = (1920, 1080)  # Maximum dimensions for images
    MAX_IMAGE_QUALITY = 85  # JPEG quality (0-100)
    
    @staticmethod
    def process_image(image_file):
        """
        Process and compress an image file.
        Returns the processed file path.
        """
        try:
            # Open the image
            img = Image.open(image_file)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
            
            # Resize if necessary
            if img.size[0] > MediaProcessor.MAX_IMAGE_SIZE[0] or img.size[1] > MediaProcessor.MAX_IMAGE_SIZE[1]:
                img.thumbnail(MediaProcessor.MAX_IMAGE_SIZE, Image.LANCZOS)
            
            # Save the processed image
            output = tempfile.NamedTemporaryFile(suffix='.jpg')
            img.save(output, format='JPEG', quality=MediaProcessor.MAX_IMAGE_QUALITY, optimize=True)
            
            return output.name
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return None
    
    @staticmethod
    def process_video(video_file):
        """
        No video processing - return None to use original file
        """
        print("Video processing disabled - using original file")
        return None
    
    @staticmethod
    def process_media(file):
        """
        Process media file based on type
        """
        if hasattr(file, 'content_type') and file.content_type.startswith('image/'):
            return MediaProcessor.process_image(file)
        else:
            # For videos, return None to use original file
            return None
    
    @staticmethod
    def get_file_type(file):
        """
        Determine the file type using content type
        """
        if hasattr(file, 'content_type'):
            return file.content_type
        return 'application/octet-stream'