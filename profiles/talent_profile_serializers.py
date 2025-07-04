import mimetypes
from rest_framework import serializers
from .models import TalentMedia, TalentUserProfile, SocialMediaLinks
from django.utils import timezone
from .utils.file_validators import validate_video_file, validate_image_file



#to great media for talent profile
class TalentMediaSerializer(serializers.ModelSerializer):
    sharing_status = serializers.SerializerMethodField()
    media_type = serializers.CharField(read_only=True)
    media_file = serializers.FileField(required=True)
    media_info = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False)
    thumbnail = serializers.ImageField(read_only=True)
    talent = serializers.PrimaryKeyRelatedField(queryset=TalentUserProfile.objects.all(), required=False)
    
    class Meta:
        model = TalentMedia
        fields = ['id', 'talent', 'name', 'media_info', 'media_type', 'media_file', 'thumbnail', 
                 'created_at', 'updated_at', 'is_test_video', 'test_video_number', 'is_about_yourself_video', 'sharing_status']
        read_only_fields = ['id', 'created_at']
        
    def validate_media_file(self, value):
        # Determine file type
        mime_type, _ = mimetypes.guess_type(value.name)
        if mime_type is None:
            raise serializers.ValidationError("Could not determine file type.")
        
        # Use centralized validation
        try:
            if mime_type.startswith('image/'):
                validate_image_file(value)
            elif mime_type.startswith('video/'):
                validate_video_file(value)
            else:
                raise serializers.ValidationError("Unsupported file type. Only images and videos are allowed.")
        except Exception as e:
            raise serializers.ValidationError(str(e))

        return value

    def get_sharing_status(self, obj):
        """Get sharing status using centralized utility"""
        from dashboard.utils import get_sharing_status
        return get_sharing_status(obj)




class SocialMediaLinksSerializer(serializers.ModelSerializer):
    links=serializers.SerializerMethodField()
    class Meta:
        model=SocialMediaLinks
        fields =['user','facebook','twitter','instagram','linkedin','youtube','tiktok','snapchat','links']
    
    def get_links(self,obj):
        """
        Fetch and serialize the user's socillinks.
        """
        links = {}
        if obj:
            links = {
                'facebook': obj.facebook,
                'twitter': obj.twitter,
                'instagram': obj.instagram,
                'linkedin': obj.linkedin,
                'youtube': obj.youtube,
                'tiktok': obj.tiktok,
                'snapchat': obj.snapchat
            }
        return links


#to tack data from database to profile
class TalentUserProfileSerializer(serializers.ModelSerializer):
    media = TalentMediaSerializer(many=True, read_only=True)
    social_media_links = SocialMediaLinksSerializer(read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    profile_score = serializers.SerializerMethodField()

    class Meta:
        model = TalentUserProfile
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name', 'is_verified', 'profile_complete',
            'account_type', 'country', 'city','phone', 'profile_picture', 'aboutyou',
            'date_of_birth', 'gender', 'media', 'social_media_links', 'aboutyou', 'profile_score'
        ]
        extra_kwargs = {
            'user': {'read_only': True},
            'is_verified': {'read_only': True},
            'profile_complete': {'read_only': True},
            'account_type': {'read_only': True},
            'email': {'read_only': True},
            'is_verified': {'read_only':True},
            'aboutyou': {'required': False}  # Make aboutyou optional
            
        }
        
    def get_full_name(self, obj):
        """Combine first_name and last_name into a single field"""
        first_name = obj.user.first_name or ''
        last_name = obj.user.last_name or ''
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        return ""

    def get_profile_score(self, obj):
        """Get the profile score from the model's method"""
        return obj.get_profile_score()


#update in profile        
class TalentUserProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    
    def validate_phone(self, value):
        if value:
            # Basic phone number validation - allows for international format
            import re
            pattern = r'^\+?[1-9]\d{1,14}$'
            if not re.match(pattern, value):
                raise serializers.ValidationError("Please enter a valid phone number.")
        return value

    def validate_date_of_birth(self, value):
        if value:
            from django.utils import timezone
            if value > timezone.now().date():
                raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value
    
    def validate(self, data):
        # Ensure at least one field is being updated
        if not data:
            raise serializers.ValidationError("At least one field must be provided for update.")
        return data

    class Meta:
        model = TalentUserProfile
        fields = [
            'first_name', 'last_name',
            'profile_picture', 'aboutyou', 'city', 'country',
            'gender', 'date_of_birth', 'phone', 'zipcode'
        ]
        extra_kwargs = {
            'profile_picture': {'required': False},
            'aboutyou': {'required': False},
            'city': {'required': False},
            'country': {'required': False},
            'gender': {'required': False},
            'date_of_birth': {'required': False},
            'phone': {'required': False}
        }

    def update(self, instance, validated_data):
        # Handle user-related fields
        user = instance.user
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        # Update profile fields
        profile_fields = ['phone', 'zipcode', 'aboutyou', 'city', 'country', 'gender', 'date_of_birth', 'profile_picture']
        for field in profile_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        instance.save()
        return instance
    




