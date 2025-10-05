from rest_framework import serializers
from profiles.models import (
    TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker, BackGroundJobsProfile, 
    Prop, Costume, Location, Memorabilia, Vehicle, ArtisticMaterial, MusicItem, RareItem,
    Band, BandMembership, BandMedia
)
from users.models import BaseUser
import datetime
from .models import SharedMediaPost
from django.contrib.contenttypes.models import ContentType
from payments.models_restrictions import RestrictedCountryUser
from .utils import get_sharing_status

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for restricted users view"""
    class Meta:
        model = BaseUser
        fields = ['id', 'email', 'first_name', 'last_name', 'country', 'residency', 'city']

class TalentDashboardSerializer(serializers.ModelSerializer):
    """Basic user serializer for restricted users view"""
    user = UserBasicSerializer(read_only=True)
    age = serializers.SerializerMethodField()
    specialization_types = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    profile_score = serializers.SerializerMethodField()
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = TalentUserProfile
        fields = ['id', 'email', 'user', 'gender', 'city', 'country', 'date_of_birth', 'age', 
                 'profile_picture', 'is_verified', 'account_type', 'profile_complete',
                 'specialization_types', 'media_count', 'profile_score']
        read_only_fields = ['id', 'email', 'user', 'is_verified', 'profile_complete', 'account_type']
    
    def get_age(self, obj):
        if obj.date_of_birth:
            today = datetime.date.today()
            return today.year - obj.date_of_birth.year - ((today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day))
        return None
    
    def get_specialization_types(self, obj):
        specializations = []
        if hasattr(obj, 'visual_worker'):
            specializations.append(f"Visual: {obj.visual_worker.get_primary_category_display()}")
        if hasattr(obj, 'expressive_worker'):
            specializations.append(f"Expressive: {obj.expressive_worker.get_performer_type_display()}")
        if hasattr(obj, 'hybrid_worker'):
            specializations.append(f"Hybrid: {obj.hybrid_worker.get_hybrid_type_display()}")
        return specializations
    
    def get_media_count(self, obj):
        return {
            'images': obj.media.filter(media_type='image').count(),
            'videos': obj.media.filter(media_type='video').count()
        }
    
    def get_profile_score(self, obj):
        # Start with breakdown of score components
        score_breakdown = {
            'total': 0,
            'account_tier': 0,
            'verification': 0,
            'profile_completion': 0,
            'media_content': 0,
            'specializations': 0,
            'details': {}
        }
        
        # Score for account tier
        if obj.account_type == 'platinum':
            score_breakdown['account_tier'] = 25
            score_breakdown['details']['account_tier'] = 'Platinum account: +25 points'
        elif obj.account_type == 'premium':
            score_breakdown['account_tier'] = 15
            score_breakdown['details']['account_tier'] = 'Premium account: +15 points'
        else:
            score_breakdown['account_tier'] = 5
            score_breakdown['details']['account_tier'] = 'Free account: +5 points'
        
        # Score for verification
        if obj.is_verified:
            score_breakdown['verification'] = 20
            score_breakdown['details']['verification'] = 'Verified profile: +20 points'
        else:
            score_breakdown['details']['verification'] = 'Not verified: +0 points (get verified for +20 points)'
        
        # Score for profile completion
        if obj.profile_complete:
            score_breakdown['profile_completion'] = 15
            score_breakdown['details']['profile_completion'] = 'Profile complete: +15 points'
        else:
            score_breakdown['details']['profile_completion'] = 'Profile incomplete: +0 points (complete your profile for +15 points)'
        
        # Score for media content
        media_count = obj.media.count()
        if media_count > 20:
            score_breakdown['media_content'] = 25
            score_breakdown['details']['media_content'] = 'Extensive media (20+ items): +25 points'
        elif media_count > 10:
            score_breakdown['media_content'] = 20
            score_breakdown['details']['media_content'] = 'Rich media (10-20 items): +20 points'
        elif media_count > 5:
            score_breakdown['media_content'] = 15
            score_breakdown['details']['media_content'] = 'Good media (5-10 items): +15 points'
        elif media_count > 0:
            score_breakdown['media_content'] = 10
            score_breakdown['details']['media_content'] = 'Basic media (1-5 items): +10 points'
        else:
            score_breakdown['details']['media_content'] = 'No media: +0 points (add media for up to +25 points)'
        
        # Score for specializations
        specialization_count = 0
        if hasattr(obj, 'visual_worker'):
            specialization_count += 1
        if hasattr(obj, 'expressive_worker'):
            specialization_count += 1
        if hasattr(obj, 'hybrid_worker'):
            specialization_count += 1
        
        score_breakdown['specializations'] = specialization_count * 10
        if specialization_count > 0:
            score_breakdown['details']['specializations'] = f'{specialization_count} specialization(s): +{specialization_count * 10} points'
        else:
            score_breakdown['details']['specializations'] = 'No specializations: +0 points (add specializations for +10 points each)'
        
        # Calculate total score
        score_breakdown['total'] = (
            score_breakdown['account_tier'] + 
            score_breakdown['verification'] + 
            score_breakdown['profile_completion'] + 
            score_breakdown['media_content'] + 
            score_breakdown['specializations']
        )
        
        # Cap the score at 100 for normalization
        score_breakdown['total'] = min(score_breakdown['total'], 100)
        
        # Include tips for improvement if score is below 80
        if score_breakdown['total'] < 80:
            score_breakdown['improvement_tips'] = []
            if obj.account_type == 'free':
                score_breakdown['improvement_tips'].append('Upgrade to Silver (+20), Gold (+30), or Platinum (+40) for more points')
            if not obj.is_verified:
                score_breakdown['improvement_tips'].append('Verify your profile for +20 points')
            if not obj.profile_complete:
                score_breakdown['improvement_tips'].append('Complete your profile for +15 points')
            if media_count < 5:
                score_breakdown['improvement_tips'].append('Add more media for up to +25 points')
            if specialization_count < 3:
                score_breakdown['improvement_tips'].append('Add more specializations for +10 points each')
        
        return score_breakdown

class VisualWorkerDashboardSerializer(serializers.ModelSerializer):
    profile = TalentDashboardSerializer(read_only=True)
    city = serializers.CharField(source='profile.city', read_only=True)
    country = serializers.CharField(source='profile.country', read_only=True)
    
    class Meta:
        model = VisualWorker
        fields = ['id', 'profile', 'primary_category', 'years_experience', 'experience_level',
                 'portfolio_link', 'availability', 'rate_range', 'city', 'country',
                 'willing_to_relocate', 'created_at', 'updated_at']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add display values for choice fields
        representation['primary_category_display'] = instance.get_primary_category_display()
        representation['experience_level_display'] = instance.get_experience_level_display()
        representation['availability_display'] = instance.get_availability_display()
        representation['rate_range_display'] = instance.get_rate_range_display()
        return representation

class ExpressiveWorkerDashboardSerializer(serializers.ModelSerializer):
    profile = TalentDashboardSerializer(read_only=True)
    city = serializers.CharField(source='profile.city', read_only=True)
    country = serializers.CharField(source='profile.country', read_only=True)
    profile_score = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpressiveWorker
        fields = [
            'id', 'profile', 'performer_type', 'years_experience', 'height', 'weight',
            'hair_color', 'hair_type', 'skin_tone', 'eye_color', 'eye_size', 'eye_pattern',
            'face_shape', 'forehead_shape', 'lip_shape', 'eyebrow_pattern',
            'beard_color', 'beard_length', 'mustache_color', 'mustache_length',
            'distinctive_facial_marks', 'distinctive_body_marks', 'voice_type',
            'body_type', 'availability', 'city', 'country',
            'created_at', 'updated_at', 'profile_score'
        ]
    
    def get_profile_score(self, obj):
        profile = obj.profile
        score = 0
        if profile.account_type == 'platinum':
            score += 25
        elif profile.account_type == 'premium':
            score += 15
        else:
            score += 5
        if profile.is_verified:
            score += 20
        if profile.profile_complete:
            score += 15
        media_count = profile.media.count() if hasattr(profile, 'media') else 0
        if media_count > 20:
            score += 25
        elif media_count > 10:
            score += 20
        elif media_count > 5:
            score += 15
        elif media_count > 0:
            score += 10
        if obj.years_experience > 10:
            score += 15
        elif obj.years_experience > 5:
            score += 10
        elif obj.years_experience > 2:
            score += 5
        new_fields = [
            'hair_type', 'skin_tone', 'eye_size', 'eye_pattern', 'face_shape', 'forehead_shape',
            'lip_shape', 'eyebrow_pattern', 'beard_color', 'beard_length', 'mustache_color',
            'mustache_length', 'distinctive_facial_marks', 'distinctive_body_marks', 'voice_type'
        ]
        for field in new_fields:
            if getattr(obj, field, None):
                score += 2
        return min(score, 100)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add display values for choice fields
        representation['performer_type_display'] = instance.get_performer_type_display()
        representation['hair_color_display'] = instance.get_hair_color_display()
        representation['eye_color_display'] = instance.get_eye_color_display()
        representation['body_type_display'] = instance.get_body_type_display()
        representation['availability_display'] = instance.get_availability_display()
        # Add display for new choice fields if needed
        if hasattr(instance, 'get_hair_type_display'):
            representation['hair_type_display'] = instance.get_hair_type_display()
        if hasattr(instance, 'get_skin_tone_display'):
            representation['skin_tone_display'] = instance.get_skin_tone_display()
        if hasattr(instance, 'get_eye_size_display'):
            representation['eye_size_display'] = instance.get_eye_size_display()
        if hasattr(instance, 'get_eye_pattern_display'):
            representation['eye_pattern_display'] = instance.get_eye_pattern_display()
        if hasattr(instance, 'get_face_shape_display'):
            representation['face_shape_display'] = instance.get_face_shape_display()
        if hasattr(instance, 'get_forehead_shape_display'):
            representation['forehead_shape_display'] = instance.get_forehead_shape_display()
        if hasattr(instance, 'get_lip_shape_display'):
            representation['lip_shape_display'] = instance.get_lip_shape_display()
        if hasattr(instance, 'get_eyebrow_pattern_display'):
            representation['eyebrow_pattern_display'] = instance.get_eyebrow_pattern_display()
        if hasattr(instance, 'get_beard_color_display'):
            representation['beard_color_display'] = instance.get_beard_color_display()
        if hasattr(instance, 'get_beard_length_display'):
            representation['beard_length_display'] = instance.get_beard_length_display()
        if hasattr(instance, 'get_mustache_color_display'):
            representation['mustache_color_display'] = instance.get_mustache_color_display()
        if hasattr(instance, 'get_mustache_length_display'):
            representation['mustache_length_display'] = instance.get_mustache_length_display()
        if hasattr(instance, 'get_distinctive_facial_marks_display'):
            representation['distinctive_facial_marks_display'] = instance.get_distinctive_facial_marks_display()
        if hasattr(instance, 'get_distinctive_body_marks_display'):
            representation['distinctive_body_marks_display'] = instance.get_distinctive_body_marks_display()
        if hasattr(instance, 'get_voice_type_display'):
            representation['voice_type_display'] = instance.get_voice_type_display()
        return representation

class HybridWorkerDashboardSerializer(serializers.ModelSerializer):
    profile = TalentDashboardSerializer(read_only=True)
    city = serializers.CharField(source='profile.city', read_only=True)
    country = serializers.CharField(source='profile.country', read_only=True)
    
    class Meta:
        model = HybridWorker
        fields = ['id', 'profile', 'hybrid_type', 'years_experience', 'height', 'weight',
                 'hair_color', 'eye_color', 'skin_tone', 'body_type', 'fitness_level',
                 'risk_levels', 'availability', 'willing_to_relocate', 'city', 'country',
                 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add display values for choice fields
        representation['hybrid_type_display'] = instance.get_hybrid_type_display()
        representation['hair_color_display'] = instance.get_hair_color_display()
        representation['eye_color_display'] = instance.get_eye_color_display()
        representation['skin_tone_display'] = instance.get_skin_tone_display()
        representation['body_type_display'] = instance.get_body_type_display()
        representation['fitness_level_display'] = instance.get_fitness_level_display()
        representation['risk_levels_display'] = instance.get_risk_levels_display()
        representation['availability_display'] = instance.get_availability_display()
        return representation

class BackgroundUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseUser
        fields = ['id', 'email', 'first_name', 'last_name']

class BackGroundDashboardSerializer(serializers.ModelSerializer):
    user = BackgroundUserSerializer(read_only=True)
    age = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    profile_score = serializers.SerializerMethodField()
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = BackGroundJobsProfile
        fields = ['id', 'email', 'user', 'country', 'date_of_birth', 'age', 'gender', 'account_type', 'item_count', 'profile_score']
        read_only_fields = ['id', 'email', 'user', 'account_type']
    
    def get_age(self, obj):
        if obj.date_of_birth:
            today = datetime.date.today()
            return today.year - obj.date_of_birth.year - ((today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day))
        return None
    
    def get_item_count(self, obj):
        # Count all items of different types related to this profile
        item_counts = {
            'props': Prop.objects.filter(BackGroundJobsProfile=obj).count(),
            'costumes': Costume.objects.filter(BackGroundJobsProfile=obj).count(),
            'locations': Location.objects.filter(BackGroundJobsProfile=obj).count(),
            'memorabilia': Memorabilia.objects.filter(BackGroundJobsProfile=obj).count(),
            'vehicles': Vehicle.objects.filter(BackGroundJobsProfile=obj).count(),
            'artistic_materials': ArtisticMaterial.objects.filter(BackGroundJobsProfile=obj).count(),
            'music_items': MusicItem.objects.filter(BackGroundJobsProfile=obj).count(),
            'rare_items': RareItem.objects.filter(BackGroundJobsProfile=obj).count(),
            'total': 0
        }
        item_counts['total'] = sum(count for key, count in item_counts.items() if key != 'total')
        return item_counts
    
    def get_profile_score(self, obj):
        # Start with breakdown of score components
        score_breakdown = {
            'total': 0,
            'account_tier': 0,
            'profile_completion': 0,
            'item_diversity': 0,
            'item_quantity': 0,
            'details': {}
        }
        
        # Score for account tier
        if obj.account_type == 'back_ground_jobs':
            score_breakdown['account_tier'] = 50
            score_breakdown['details']['account_tier'] = 'Background Jobs account: +50 points'
        else:
            score_breakdown['account_tier'] = 10
            score_breakdown['details']['account_tier'] = 'Free account: +10 points (upgrade for +40 points)'
        
        # Score for profile completeness - check basic fields
        profile_complete = bool(obj.country and obj.date_of_birth and obj.gender)
        if profile_complete:
            score_breakdown['profile_completion'] = 15
            score_breakdown['details']['profile_completion'] = 'Profile complete: +15 points'
        else:
            score_breakdown['details']['profile_completion'] = 'Profile incomplete: +0 points (complete your profile for +15 points)'
        
        # Score for item diversity (number of different item types)
        item_types = [
            Prop.objects.filter(BackGroundJobsProfile=obj).exists(),
            Costume.objects.filter(BackGroundJobsProfile=obj).exists(),
            Location.objects.filter(BackGroundJobsProfile=obj).exists(),
            Memorabilia.objects.filter(BackGroundJobsProfile=obj).exists(),
            Vehicle.objects.filter(BackGroundJobsProfile=obj).exists(),
            ArtisticMaterial.objects.filter(BackGroundJobsProfile=obj).exists(),
            MusicItem.objects.filter(BackGroundJobsProfile=obj).exists(),
            RareItem.objects.filter(BackGroundJobsProfile=obj).exists()
        ]
        
        item_type_count = sum(1 for t in item_types if t)
        score_breakdown['item_diversity'] = item_type_count * 5
        if item_type_count > 0:
            score_breakdown['details']['item_diversity'] = f'{item_type_count} item types: +{item_type_count * 5} points'
        else:
            score_breakdown['details']['item_diversity'] = 'No item types: +0 points (add different item types for +5 points each)'
        
        # Score for total item quantity
        total_items = sum([
            Prop.objects.filter(BackGroundJobsProfile=obj).count(),
            Costume.objects.filter(BackGroundJobsProfile=obj).count(),
            Location.objects.filter(BackGroundJobsProfile=obj).count(),
            Memorabilia.objects.filter(BackGroundJobsProfile=obj).count(),
            Vehicle.objects.filter(BackGroundJobsProfile=obj).count(),
            ArtisticMaterial.objects.filter(BackGroundJobsProfile=obj).count(),
            MusicItem.objects.filter(BackGroundJobsProfile=obj).count(),
            RareItem.objects.filter(BackGroundJobsProfile=obj).count()
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
        
        # Calculate total score
        score_breakdown['total'] = (
            score_breakdown['account_tier'] + 
            score_breakdown['profile_completion'] + 
            score_breakdown['item_diversity'] + 
            score_breakdown['item_quantity']
        )
        
        # Cap the score at 100 for normalization
        score_breakdown['total'] = min(score_breakdown['total'], 100)
        
        # Include tips for improvement if score is below 80
        if score_breakdown['total'] < 80:
            score_breakdown['improvement_tips'] = []
            if obj.account_type != 'back_ground_jobs':
                score_breakdown['improvement_tips'].append('Upgrade to Background Jobs account for +40 points')
            if not profile_complete:
                score_breakdown['improvement_tips'].append('Complete your profile for +15 points')
            if item_type_count < 8:
                score_breakdown['improvement_tips'].append('Add more item types for +5 points each')
            if total_items < 5:
                score_breakdown['improvement_tips'].append('Add more items for up to +25 points')
        
        return score_breakdown

class BackgroundProfileBasicSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BackGroundJobsProfile
        fields = ['id', 'user_email', 'user_name']
    
    def get_user_name(self, obj):
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.email

class PropDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    sharing_status = serializers.SerializerMethodField()
    email = serializers.CharField(source='BackGroundJobsProfile.user.email', read_only=True)
    
    class Meta:
        model = Prop
        fields = ['id', 'email', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'material', 'used_in_movie', 'condition', 'created_at', 'updated_at', 'image', 'owner', 'sharing_status']
        read_only_fields = ['id', 'email', 'owner', 'created_at', 'updated_at']
    
    def get_sharing_status(self, obj):
        """Get sharing status information for the prop using centralized utility"""
        return get_sharing_status(obj)

class CostumeDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    sharing_status = serializers.SerializerMethodField()
    email = serializers.CharField(source='BackGroundJobsProfile.user.email', read_only=True)
    
    class Meta:
        model = Costume
        fields = ['id', 'email', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'size', 'worn_by', 'era', 'created_at', 'updated_at', 'image', 'owner', 'sharing_status']
        read_only_fields = ['id', 'email', 'owner', 'created_at', 'updated_at']
    
    def get_sharing_status(self, obj):
        """Get sharing status information for the costume using centralized utility"""
        return get_sharing_status(obj)

class LocationDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    sharing_status = serializers.SerializerMethodField()
    email = serializers.CharField(source='BackGroundJobsProfile.user.email', read_only=True)
    
    class Meta:
        model = Location
        fields = ['id', 'email', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'address', 'capacity', 'is_indoor', 'created_at', 'updated_at', 'image', 'owner', 'sharing_status']
        read_only_fields = ['id', 'email', 'owner', 'created_at', 'updated_at']
    
    def get_sharing_status(self, obj):
        """Get sharing status information for the location using centralized utility"""
        return get_sharing_status(obj)

class MemorabilaDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    sharing_status = serializers.SerializerMethodField()
    email = serializers.CharField(source='BackGroundJobsProfile.user.email', read_only=True)
    
    class Meta:
        model = Memorabilia
        fields = ['id', 'email', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'signed_by', 'authenticity_certificate', 'created_at', 'updated_at', 'image', 'owner', 'sharing_status']
        read_only_fields = ['id', 'email', 'owner', 'created_at', 'updated_at']
    
    def get_sharing_status(self, obj):
        """Get sharing status information for the memorabilia using centralized utility"""
        return get_sharing_status(obj)

class VehicleDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    sharing_status = serializers.SerializerMethodField()
    email = serializers.CharField(source='BackGroundJobsProfile.user.email', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = ['id', 'email', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'make', 'model', 'year', 'condition', 'created_at', 'updated_at', 'image', 'owner', 'sharing_status']
        read_only_fields = ['id', 'email', 'owner', 'created_at', 'updated_at']
    
    def get_sharing_status(self, obj):
        """Get sharing status information for the vehicle using centralized utility"""
        return get_sharing_status(obj)

class ArtisticMaterialDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    sharing_status = serializers.SerializerMethodField()
    email = serializers.CharField(source='BackGroundJobsProfile.user.email', read_only=True)
    
    class Meta:
        model = ArtisticMaterial
        fields = ['id', 'email', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'type', 'condition', 'created_at', 'updated_at', 'image', 'owner', 'sharing_status']
        read_only_fields = ['id', 'email', 'owner', 'created_at', 'updated_at']
    
    def get_sharing_status(self, obj):
        """Get sharing status information for the artistic material using centralized utility"""
        return get_sharing_status(obj)

class MusicItemDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    sharing_status = serializers.SerializerMethodField()
    email = serializers.CharField(source='BackGroundJobsProfile.user.email', read_only=True)
    
    class Meta:
        model = MusicItem
        fields = ['id', 'email', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'instrument_type', 'condition', 'created_at', 'updated_at', 'image', 'owner', 'sharing_status']
        read_only_fields = ['id', 'email', 'owner', 'created_at', 'updated_at']
    
    def get_sharing_status(self, obj):
        """Get sharing status information for the music item using centralized utility"""
        return get_sharing_status(obj)

class RareItemDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    sharing_status = serializers.SerializerMethodField()
    email = serializers.CharField(source='BackGroundJobsProfile.user.email', read_only=True)
    
    class Meta:
        model = RareItem
        fields = ['id', 'email', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'provenance', 'is_one_of_a_kind', 'created_at', 'updated_at', 'image', 'owner', 'sharing_status']
        read_only_fields = ['id', 'email', 'owner', 'created_at', 'updated_at']
    
    def get_sharing_status(self, obj):
        """Get sharing status information for the rare item using centralized utility"""
        return get_sharing_status(obj)

class BandMemberDashboardSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()
    profile_id = serializers.SerializerMethodField()
    
    def get_member_name(self, obj):
        if obj.talent_user and hasattr(obj.talent_user, 'user'):
            user = obj.talent_user.user
            if user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            return user.email
        return "Unknown Member"
    
    def get_profile_id(self, obj):
        if obj.talent_user:
            return obj.talent_user.id
        return None
    
    class Meta:
        model = BandMembership
        fields = ['id', 'member_name', 'profile_id', 'role', 'position', 'date_joined']

class BandMediaDashboardSerializer(serializers.ModelSerializer):
    sharing_status = serializers.SerializerMethodField()
    
    class Meta:
        model = BandMedia
        fields = ['id', 'name', 'media_info', 'media_type', 'media_file', 'created_at', 'sharing_status']
    
    def get_sharing_status(self, obj):
        """
        Get sharing status for a band media item using centralized utility.
        """
        return get_sharing_status(obj)

class BandDashboardSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    creator_id = serializers.SerializerMethodField()
    creator_email = serializers.CharField(source='creator.user.email', read_only=True)
    media = BandMediaDashboardSerializer(many=True, read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    admin_count = serializers.IntegerField(read_only=True)
    profile_score = serializers.SerializerMethodField()
    
    def get_members(self, obj):
        memberships = obj.members.all()
        return BandMemberDashboardSerializer(memberships, many=True).data
    
    def get_creator_name(self, obj):
        if obj.creator and obj.creator.user:
            return f"{obj.creator.user.first_name} {obj.creator.user.last_name}".strip() or obj.creator.user.email
        return "Unknown"
    
    def get_creator_id(self, obj):
        return obj.creator.user.id if obj.creator and obj.creator.user else None
    
    def get_profile_score(self, obj):
        # Start with breakdown of score components
        score_breakdown = {
            'total': 0,
            'profile_completion': 0,
            'media_content': 0,
            'member_count': 0,
            'band_details': 0,
            'details': {}
        }
        
        # Score for profile completion
        profile_fields = [
            bool(obj.name), bool(obj.description), bool(obj.band_type), 
            bool(obj.profile_picture), bool(obj.contact_email or obj.contact_phone), 
            bool(obj.location)
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
        
        # Score for media content
        media_count = obj.media.count()
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
        
        # Score for member count
        member_count = obj.member_count
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
        
        # Score for band details (positions, etc.)
        members_with_positions = BandMembership.objects.filter(band=obj, position__isnull=False).exclude(position='').count()
        if members_with_positions == member_count and member_count > 0:
            score_breakdown['band_details'] = 10
            score_breakdown['details']['band_details'] = 'All members have positions: +10 points'
        elif members_with_positions > 0:
            score_breakdown['band_details'] = 5
            score_breakdown['details']['band_details'] = 'Some members have positions: +5 points'
        else:
            score_breakdown['details']['band_details'] = 'No member positions: +0 points (add positions for up to +10 points)'
        
        # Calculate total score
        score_breakdown['total'] = (
            score_breakdown['profile_completion'] + 
            score_breakdown['media_content'] + 
            score_breakdown['member_count'] + 
            score_breakdown['band_details']
        )
        
        # Cap the score at 100 for normalization
        score_breakdown['total'] = min(score_breakdown['total'], 100)
        
        # Include tips for improvement if score is below 80
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
    
    class Meta:
        model = Band
        fields = [
            'id', 'creator_email', 'name', 'band_type', 'location', 'description',
            'creator_name', 'creator_id', 'members', 'media', 'member_count', 'admin_count',
            'created_at', 'updated_at', 'profile_score'
        ]
        read_only_fields = ['id', 'creator_email', 'creator_name', 'creator_id', 'members', 'media', 'member_count', 'admin_count', 'created_at', 'updated_at']

# Email-related serializers for bulk email functionality
from .models import BulkEmail, EmailRecipient

class BulkEmailSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BulkEmail
        fields = ['id', 'sender', 'sender_name', 'subject', 'message', 'search_criteria',
                 'status', 'total_recipients', 'emails_sent', 'emails_failed', 
                 'created_at', 'sent_at']
        read_only_fields = ['sender', 'total_recipients', 'emails_sent', 'emails_failed', 'sent_at']
    
    def get_sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email

class EmailListSerializer(serializers.ModelSerializer):
    """Serializer for email list with recipient information"""
    sender_name = serializers.SerializerMethodField()
    recipient_email = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    recipient_status = serializers.SerializerMethodField()
    
    class Meta:
        model = BulkEmail
        fields = ['id', 'sender', 'sender_name', 'subject', 'message', 'search_criteria',
                 'status', 'total_recipients', 'emails_sent', 'emails_failed', 
                 'created_at', 'sent_at', 'recipient_email', 'recipient_name', 'recipient_status']
        read_only_fields = ['sender', 'total_recipients', 'emails_sent', 'emails_failed', 'sent_at']
    
    def get_sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email
    
    def get_recipient_email(self, obj):
        recipient = obj.recipients.first()
        return recipient.user.email if recipient else None
    
    def get_recipient_name(self, obj):
        recipient = obj.recipients.first()
        if recipient:
            return f"{recipient.user.first_name} {recipient.user.last_name}".strip() or recipient.user.email
        return None
    
    def get_recipient_status(self, obj):
        recipient = obj.recipients.first()
        return recipient.status if recipient else None

class EmailRecipientSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = EmailRecipient
        fields = ['id', 'user', 'user_name', 'user_email', 'status', 'error_message', 'sent_at']
        read_only_fields = ['status', 'error_message', 'sent_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email 

class SharedMediaPostSerializer(serializers.ModelSerializer):
    """Serializer for viewing shared media posts"""
    shared_by_name = serializers.CharField(source='shared_by.get_full_name', read_only=True)
    shared_by_email = serializers.CharField(source='shared_by.email', read_only=True)
    content_info = serializers.SerializerMethodField()
    attribution_text = serializers.SerializerMethodField()
    original_owner = serializers.SerializerMethodField()
    
    class Meta:
        model = SharedMediaPost
        fields = [
            'id', 'caption', 'category', 'shared_at', 'is_active',
            'shared_by_name', 'shared_by_email', 'content_info', 
            'attribution_text', 'original_owner'
        ]
    
    def get_content_info(self, obj):
        return obj.get_content_info()
    
    def get_attribution_text(self, obj):
        return obj.get_attribution_text()
    
    def get_original_owner(self, obj):
        owner = obj.get_original_owner()
        if owner:
            return {
                'id': owner.id,
                'name': f"{owner.first_name} {owner.last_name}",
                'email': owner.email
            }
        return None

class ShareMediaSerializer(serializers.Serializer):
    """Serializer for creating shared media posts"""
    content_type = serializers.CharField(help_text="Type of content: 'talent_media', 'band_media', 'prop', 'costume', etc.")
    object_id = serializers.IntegerField(help_text="ID of the content to share")
    caption = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    category = serializers.ChoiceField(
        choices=SharedMediaPost.CATEGORY_CHOICES,
        default='general',
        required=False
    )
    
    def validate_content_type(self, value):
        """Validate that content_type is valid"""
        valid_types = {
            'talent_media': 'profiles.TalentMedia',
            'band_media': 'profiles.BandMedia',
            'prop': 'profiles.Prop',
            'costume': 'profiles.Costume',
            'location': 'profiles.Location',
            'memorabilia': 'profiles.Memorabilia',
            'vehicle': 'profiles.Vehicle',
            'artistic_material': 'profiles.ArtisticMaterial',
            'music_item': 'profiles.MusicItem',
            'rare_item': 'profiles.RareItem',
        }
        
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid content_type. Must be one of: {', '.join(valid_types.keys())}"
            )
        
        return valid_types[value]
    
    def validate(self, data):
        """Validate that the object exists and can be shared"""
        content_type_str = data['content_type']
        object_id = data['object_id']
        
        try:
            # Get the ContentType
            app_label, model_name = content_type_str.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
            
            # Check if object exists
            model_class = content_type.model_class()
            obj = model_class.objects.get(id=object_id)
            
            # Store for later use
            data['content_type_obj'] = content_type
            data['shared_object'] = obj
            
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Invalid content type")
        except Exception as e:
            raise serializers.ValidationError("Content not found")
        
        return data
    
    def create(self, validated_data):
        """Create a new shared media post"""
        # Remove our custom fields and the original fields that we handle separately
        content_type_obj = validated_data.pop('content_type_obj')
        shared_object = validated_data.pop('shared_object')
        validated_data.pop('content_type', None)  # Remove the original content_type field
        validated_data.pop('object_id', None)     # Remove the original object_id field
        
        # Create the shared post
        shared_post = SharedMediaPost.objects.create(
            shared_by=self.context['request'].user,
            content_type=content_type_obj,
            object_id=shared_object.id,
            **validated_data
        )
        
        return shared_post

class SharedMediaPostListSerializer(serializers.ModelSerializer):
    """Serializer for listing shared media posts in gallery"""
    shared_by_name = serializers.CharField(source='shared_by.get_full_name', read_only=True)
    content_info = serializers.SerializerMethodField()
    attribution_text = serializers.SerializerMethodField()
    
    class Meta:
        model = SharedMediaPost
        fields = [
            'id', 'caption', 'category', 'shared_at',
            'shared_by_name', 'content_info', 'attribution_text'
        ]
    
    def get_content_info(self, obj):
        return obj.get_content_info()
    
    def get_attribution_text(self, obj):
        return obj.get_attribution_text() 

class RestrictedCountryUserSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    last_updated_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = RestrictedCountryUser
        fields = [
            'id', 'user', 'country', 'account_type', 'is_approved', 
            'notes', 'created_at', 'updated_at', 'last_updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at'] 
