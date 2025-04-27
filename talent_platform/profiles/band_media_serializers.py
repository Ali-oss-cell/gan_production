import mimetypes
from rest_framework import serializers
from .models import BandMedia, Band, BandMembership

class BandMediaSerializer(serializers.ModelSerializer):
    media_type = serializers.CharField(read_only=True)
    media_file = serializers.FileField(required=True)
    media_info = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False)
    band_name = serializers.CharField(source='band.name', read_only=True)
    
    class Meta:
        model = BandMedia
        fields = ['id', 'band', 'band_name', 'media_type', 'media_file', 'created_at', 'updated_at', 'name', 'media_info']
        read_only_fields = ['id', 'created_at', 'updated_at', 'band_name']
        
    def validate_media_file(self, value):
        max_size = 100 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("The maximum file size that can be uploaded is 100MB.")

        mime_type, _ = mimetypes.guess_type(value.name)
        if mime_type is None:
            raise serializers.ValidationError("Could not determine file type.")
        
        if mime_type.startswith('image/'):
            valid_mime_types = ['image/jpeg', 'image/png', 'image/jpg']
        elif mime_type.startswith('video/'):
            valid_mime_types = ['video/mp4', 'video/mkv', 'video/MOV', 'video/Wmv']
        else:
            raise serializers.ValidationError("Unsupported file type. Only images and videos are allowed.")

        if mime_type not in valid_mime_types:
            raise serializers.ValidationError(f"Only {', '.join(valid_mime_types)} formats are allowed for {mime_type.split('/')[0]}s.")

        return value
    
    def validate(self, data):
        # Check if the band exists
        band = data.get('band')
        if not band:
            raise serializers.ValidationError("Band is required.")
        
        # Check media type limits
        media_file = data.get('media_file')
        if not media_file:
            return data
            
        mime_type, _ = mimetypes.guess_type(media_file.name)
        media_type = 'image' if mime_type and mime_type.startswith('image/') else 'video'
        
        # Check if the band has reached the limit of 3 images or 3 videos
        if media_type == 'image' and band.media.filter(media_type='image').count() >= 3:
            raise serializers.ValidationError("A band can have a maximum of 3 images.")
        elif media_type == 'video' and band.media.filter(media_type='video').count() >= 3:
            raise serializers.ValidationError("A band can have a maximum of 3 videos.")
            
        return data