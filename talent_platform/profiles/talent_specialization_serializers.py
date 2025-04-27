from rest_framework import serializers
from .models import VisualWorker, ExpressiveWorker, HybridWorker

class VisualWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisualWorker
        fields = [
            'viganras', 'modeling_experience', 'preferred_styles', 'portfolio_link',
            'measurements', 'shoe_size', 'piercing_locations', 'availability',
            'preferred_work', 'certifications', 'influencer_niche', 'engagement_rate'
        ]
        
class ExpressiveWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpressiveWorker
        fields = [
            'exganras', 'performance_skill', 'acting_experience', 'vocal_range',
            'awards', 'training', 'languages_spoken', 'accents'
        ]

class HybridWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = HybridWorker
        fields = [
            'hyganras', 'performance_skill', 'fitness_level', 'running_speed',
            'jump_height', 'flexibility_level', 'body_type', 'chest_size',
            'waist_size', 'hip_size', 'dance_style', 'martial_arts_skills',
            'acrobatic_skills', 'stunt_experience', 'performance_videos',
            'social_media_links', 'availability', 'preferred_roles',
            'certifications', 'training', 'special_skills', 'awards'
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
            # Update existing specialization
            for key, value in data.items():
                setattr(specialization, key, value)
            specialization.save()
        except AttributeError:
            # Create new specialization
            data['profile'] = profile
            specialization = model_class.objects.create(**data)
        
        return specialization
    
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