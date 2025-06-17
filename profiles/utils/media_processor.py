import os
from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from imagekit.processors import ResizeToFit
from imagekit.models import ProcessedImageField
import magic
import subprocess
import tempfile
import shutil

class MediaProcessor:
    MAX_IMAGE_SIZE = (1920, 1080)  # Maximum dimensions for images
    MAX_IMAGE_QUALITY = 85  # JPEG quality (0-100)
    MAX_VIDEO_BITRATE = '1500k'  # Maximum video bitrate for 720p
    MAX_VIDEO_RESOLUTION = '1280x720'  # Fixed 720p resolution for all videos
    
    @staticmethod
    def _is_ffmpeg_available():
        """Check if FFmpeg is available on the system"""
        return shutil.which('ffmpeg') is not None
    
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
        Process and compress a video file using FFmpeg.
        All videos are standardized to 720p resolution for optimal storage and streaming.
        Returns the processed file path, or None if FFmpeg is not available.
        """
        # Check if FFmpeg is available
        if not MediaProcessor._is_ffmpeg_available():
            print("Warning: FFmpeg not found. Video processing disabled. Videos will be used as-is.")
            return None
        
        try:
            # Create a temporary file for the output
            output = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            
            # FFmpeg command for video compression to 720p
            cmd = [
                'ffmpeg',
                '-i', video_file,
                '-vf', f'scale={MediaProcessor.MAX_VIDEO_RESOLUTION}:force_original_aspect_ratio=decrease,pad={MediaProcessor.MAX_VIDEO_RESOLUTION}:(ow-iw)/2:(oh-ih)/2',
                '-b:v', MediaProcessor.MAX_VIDEO_BITRATE,
                '-maxrate', '1800k',
                '-bufsize', '3000k',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',  # Optimize for web streaming
                output.name
            ]
            
            # Run FFmpeg command
            subprocess.run(cmd, check=True, capture_output=True)
            
            return output.name
            
        except Exception as e:
            print(f"Error processing video: {str(e)}")
            return None
    
    @staticmethod
    def get_file_type(file):
        """
        Determine the file type using python-magic.
        """
        mime = magic.Magic(mime=True)
        return mime.from_buffer(file.read(2048))
    
    @staticmethod
    def process_media(media_file):
        """
        Process media file based on its type.
        Returns the processed file path, or None if processing is not available.
        """
        file_type = MediaProcessor.get_file_type(media_file)
        
        if file_type.startswith('image/'):
            return MediaProcessor.process_image(media_file)
        elif file_type.startswith('video/'):
            return MediaProcessor.process_video(media_file)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")