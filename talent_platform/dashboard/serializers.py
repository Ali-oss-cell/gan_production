from rest_framework import serializers
from profiles.models import (
    TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker, BackGroundJobsProfile, 
    Prop, Costume, Location, Memorabilia, Vehicle, ArtisticMaterial, MusicItem, RareItem,
    Band, BandMembership, BandMedia
)
from users.models import BaseUser
import datetime

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']

class TalentDashboardSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    age = serializers.SerializerMethodField()
    specialization_types = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TalentUserProfile
        fields = ['id', 'user', 'gender', 'city', 'country', 'date_of_birth', 'age', 
                 'profile_picture', 'is_verified', 'account_type', 'profile_complete',
                 'specialization_types', 'media_count']
    
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

class VisualWorkerDashboardSerializer(serializers.ModelSerializer):
    profile = TalentDashboardSerializer(read_only=True)
    
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
    
    class Meta:
        model = ExpressiveWorker
        fields = ['id', 'profile', 'performer_type', 'years_experience', 'height', 'weight',
                 'hair_color', 'eye_color', 'body_type', 'availability', 'city', 'country',
                 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add display values for choice fields
        representation['performer_type_display'] = instance.get_performer_type_display()
        representation['hair_color_display'] = instance.get_hair_color_display()
        representation['eye_color_display'] = instance.get_eye_color_display()
        representation['body_type_display'] = instance.get_body_type_display()
        representation['availability_display'] = instance.get_availability_display()
        return representation

class HybridWorkerDashboardSerializer(serializers.ModelSerializer):
    profile = TalentDashboardSerializer(read_only=True)
    
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
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']

class BackGroundDashboardSerializer(serializers.ModelSerializer):
    user = BackgroundUserSerializer(read_only=True)
    age = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BackGroundJobsProfile
        fields = ['id', 'user', 'country', 'date_of_birth', 'age', 'gender', 'account_type', 'item_count']
    
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

class BackgroundProfileBasicSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BackGroundJobsProfile
        fields = ['id', 'user_email', 'user_name']
    
    def get_user_name(self, obj):
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.username

class PropDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    
    class Meta:
        model = Prop
        fields = ['id', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'material', 'used_in_movie', 'condition', 'created_at', 'updated_at', 'image', 'owner']

class CostumeDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    
    class Meta:
        model = Costume
        fields = ['id', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'size', 'worn_by', 'era', 'created_at', 'updated_at', 'image', 'owner']

class LocationDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    
    class Meta:
        model = Location
        fields = ['id', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'address', 'capacity', 'is_indoor', 'created_at', 'updated_at', 'image', 'owner']

class MemorabilaDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    
    class Meta:
        model = Memorabilia
        fields = ['id', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'signed_by', 'authenticity_certificate', 'created_at', 'updated_at', 'image', 'owner']

class VehicleDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = ['id', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'make', 'model', 'year', 'created_at', 'updated_at', 'image', 'owner']

class ArtisticMaterialDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    
    class Meta:
        model = ArtisticMaterial
        fields = ['id', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'type', 'condition', 'created_at', 'updated_at', 'image', 'owner']

class MusicItemDashboardSerializer(serializers.ModelSerializer):
    owner = BackgroundProfileBasicSerializer(source='BackGroundJobsProfile', read_only=True)
    
    class Meta:
        model = MusicItem
        fields = ['id', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
                 'instrument_type', 'used_by', 'created_at', 'updated_at', 'image', 'owner']

class RareItemDashboardSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    
    def get_owner_name(self, obj):
        if obj.BackGroundJobsProfile and hasattr(obj.BackGroundJobsProfile, 'user'):
            return obj.BackGroundJobsProfile.user.username
        return "Unknown"
    
    class Meta:
        model = RareItem
        fields = ['id', 'name', 'description', 'price', 'is_for_rent', 'is_for_sale', 
                  'provenance', 'is_one_of_a_kind', 'owner_name', 'image']

class BandMemberDashboardSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()
    profile_id = serializers.SerializerMethodField()
    
    def get_member_name(self, obj):
        if obj.talent_user and hasattr(obj.talent_user, 'user'):
            return obj.talent_user.user.username
        return "Unknown Member"
    
    def get_profile_id(self, obj):
        if obj.talent_user:
            return obj.talent_user.id
        return None
    
    class Meta:
        model = BandMembership
        fields = ['id', 'member_name', 'profile_id', 'role', 'position', 'date_joined']

class BandMediaDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BandMedia
        fields = ['id', 'name', 'media_info', 'media_type', 'media_file', 'created_at']

class BandDashboardSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    creator_id = serializers.SerializerMethodField()
    media = BandMediaDashboardSerializer(many=True, read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    admin_count = serializers.IntegerField(read_only=True)
    
    def get_members(self, obj):
        memberships = BandMembership.objects.filter(band=obj).select_related('talent_user', 'talent_user__user')
        return BandMemberDashboardSerializer(memberships, many=True).data
    
    def get_creator_name(self, obj):
        if obj.creator and hasattr(obj.creator, 'user'):
            return obj.creator.user.username
        return "Unknown Creator"
    
    def get_creator_id(self, obj):
        if obj.creator:
            return obj.creator.id
        return None
    
    class Meta:
        model = Band
        fields = [
            'id', 'name', 'description', 'band_type', 'profile_picture', 
            'contact_email', 'contact_phone', 'location', 'website',
            'member_count', 'admin_count', 'members', 'creator_name', 
            'creator_id', 'media', 'created_at', 'updated_at'
        ] 