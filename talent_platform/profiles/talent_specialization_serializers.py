from rest_framework import serializers
from collections import OrderedDict
from .models import (
    VisualWorker, ExpressiveWorker, HybridWorker,
    Language, PerformanceSkill, PhysicalSkill, PerformanceGenre,
    StuntSpecialty, VisualStyle, CreativeTool, Sport, DanceStyle
)

class VisualWorkerSerializer(serializers.ModelSerializer):
    # Add nested serializers for related models
    tools = serializers.PrimaryKeyRelatedField(
        queryset=CreativeTool.objects.all(),
        many=True, required=False
    )
    styles = serializers.PrimaryKeyRelatedField(
        queryset=VisualStyle.objects.all(),
        many=True, required=False
    )
    
    class Meta:
        model = VisualWorker
        fields = [
            'primary_category', 'years_experience', 'experience_level',
            'portfolio_link', 'tools', 'styles', 'industry_sectors',
            'has_awards', 'has_professional_training', 'available_for_travel',
            'available_for_remote_work', 'availability', 'rate_range',
            'city', 'country', 'willing_to_relocate', 'languages'
        ]

class LanguageRelatedField(serializers.PrimaryKeyRelatedField):
    """Custom field for handling language proficiency"""
    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            return {}
        return OrderedDict([(item.id, str(item)) for item in queryset])

class ExpressiveWorkerSerializer(serializers.ModelSerializer):
    # Add nested serializers for related models
    performance_skills = serializers.PrimaryKeyRelatedField(
        queryset=PerformanceSkill.objects.all(),
        many=True, required=False
    )
    genres = serializers.PrimaryKeyRelatedField(
        queryset=PerformanceGenre.objects.all(),
        many=True, required=False
    )
    
    class Meta:
        model = ExpressiveWorker
        fields = [
            'performer_type', 'years_experience', 'height', 'weight',
            'age_min', 'age_max', 'hair_color', 'eye_color', 'body_type',
            'performance_skills', 'genres', 'accents', 'languages',
            'union_status', 'showreel_link', 'available_for_auditions',
            'willing_to_travel', 'has_passport', 'has_driving_license',
            'comfortable_with_stunts', 'city', 'country', 'availability'
        ]

class HybridWorkerSerializer(serializers.ModelSerializer):
    # Add nested serializers for related models
    physical_skills = serializers.PrimaryKeyRelatedField(
        queryset=PhysicalSkill.objects.all(),
        many=True, required=False
    )
    stunt_specialties = serializers.PrimaryKeyRelatedField(
        queryset=StuntSpecialty.objects.all(),
        many=True, required=False
    )
    dance_styles = serializers.PrimaryKeyRelatedField(
        queryset=DanceStyle.objects.all(),
        many=True, required=False
    )
    sports = serializers.PrimaryKeyRelatedField(
        queryset=Sport.objects.all(),
        many=True, required=False
    )
    
    class Meta:
        model = HybridWorker
        fields = [
            'hybrid_type', 'years_experience', 'height', 'weight',
            'chest', 'waist', 'hips', 'hair_color', 'eye_color',
            'skin_tone', 'body_type', 'physical_skills', 'stunt_specialties',
            'dance_styles', 'sports', 'fitness_level', 'has_stunt_insurance',
            'has_tattoos', 'has_piercings', 'has_unique_features',
            'risk_comfort', 'has_formal_training', 'certified_skills',
            'languages', 'city', 'country', 'willing_to_relocate',
            'portfolio_link'
        ]

class TalentSpecializationSerializer(serializers.Serializer):
    """Serializer for handling talent specialization selection and updates"""
    visual_worker = VisualWorkerSerializer(required=False)
    expressive_worker = ExpressiveWorkerSerializer(required=False)
    hybrid_worker = HybridWorkerSerializer(required=False)
    
    def validate(self, data):
        """Ensure at least one specialization is provided"""
        if not any([data.get('visual_worker'), data.get('expressive_worker'), data.get('hybrid_worker')]):
            raise serializers.ValidationError("At least one specialization (Visual Worker, Expressive Worker, or Hybrid Worker) must be provided.")
        return data
    
    def create_or_update_specialization(self, profile, specialization_type, data):
        """Helper method to create or update a specialization"""
        if not data:
            return None
            
        model_map = {
            'visual_worker': VisualWorker,
            'expressive_worker': ExpressiveWorker,
            'hybrid_worker': HybridWorker
        }
        
        model_class = model_map[specialization_type]
        
        # Check if specialization already exists
        try:
            specialization = getattr(profile, specialization_type)
            
            # Handle many-to-many relationships separately
            m2m_fields = self._get_m2m_fields(specialization_type)
            m2m_data = {}
            
            for field in m2m_fields:
                if field in data:
                    m2m_data[field] = data.pop(field)
            
            # Update existing specialization
            for key, value in data.items():
                setattr(specialization, key, value)
            specialization.save()
            
            # Update many-to-many relationships
            for field, value in m2m_data.items():
                getattr(specialization, field).set(value)
                
        except AttributeError:
            # Create new specialization with basic fields
            m2m_fields = self._get_m2m_fields(specialization_type)
            m2m_data = {}
            
            for field in m2m_fields:
                if field in data:
                    m2m_data[field] = data.pop(field)
            
            # Add profile to data
            data['profile'] = profile
            specialization = model_class.objects.create(**data)
            
            # Set many-to-many relationships
            for field, value in m2m_data.items():
                getattr(specialization, field).set(value)
        
        return specialization
    
    def _get_m2m_fields(self, specialization_type):
        """Helper method to identify many-to-many fields"""
        if specialization_type == 'visual_worker':
            return ['tools', 'styles', 'industry_sectors', 'languages']
        elif specialization_type == 'expressive_worker':
            return ['performance_skills', 'genres', 'accents', 'languages']
        elif specialization_type == 'hybrid_worker':
            return ['physical_skills', 'stunt_specialties', 'dance_styles', 
                   'sports', 'certified_skills', 'languages']
        return []
    
    def update(self, instance, validated_data):
        """Update the talent profile with specializations"""
        # Process each specialization type
        if 'visual_worker' in validated_data:
            self.create_or_update_specialization(
                instance, 'visual_worker', validated_data.get('visual_worker')
            )
            
        if 'expressive_worker' in validated_data:
            self.create_or_update_specialization(
                instance, 'expressive_worker', validated_data.get('expressive_worker')
            )
            
        if 'hybrid_worker' in validated_data:
            self.create_or_update_specialization(
                instance, 'hybrid_worker', validated_data.get('hybrid_worker')
            )
        
        # Update profile completion status
        instance.update_profile_completion()
        
        return instance