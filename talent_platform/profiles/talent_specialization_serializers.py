from rest_framework import serializers
from .models import VisualWorker, ExpressiveWorker, HybridWorker

class VisualWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisualWorker
        fields = [
            'primary_category', 'years_experience', 'experience_level',
            'portfolio_link', 'availability', 'rate_range',
            'city', 'country', 'willing_to_relocate'
            # Add any other simple fields from your model here
        ]

class ExpressiveWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpressiveWorker
        fields = [
            'performer_type', 'years_experience', 'height', 'weight',
            'hair_color', 'eye_color', 'body_type', 'availability',
            'city', 'country'
            # Add any other simple fields from your model here
        ]

class HybridWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = HybridWorker
        fields = [
            'hybrid_type', 'years_experience', 'height', 'weight',
            'hair_color', 'eye_color', 'skin_tone', 'body_type',
            'fitness_level', 'risk_levels', 'availability',
            'city', 'country', 'willing_to_relocate'
            # Add any other simple fields from your model here
        ]

class TalentSpecializationSerializer(serializers.Serializer):
    visual_worker = VisualWorkerSerializer(required=False)
    expressive_worker = ExpressiveWorkerSerializer(required=False)
    hybrid_worker = HybridWorkerSerializer(required=False)

    def validate(self, data):
        if not any([data.get('visual_worker'), data.get('expressive_worker'), data.get('hybrid_worker')]):
            raise serializers.ValidationError("At least one specialization (Visual Worker, Expressive Worker, or Hybrid Worker) must be provided.")
        return data

    def create_or_update_specialization(self, profile, specialization_type, data):
        if not data:
            return None
        model_map = {
            'visual_worker': VisualWorker,
            'expressive_worker': ExpressiveWorker,
            'hybrid_worker': HybridWorker
        }
        model_class = model_map[specialization_type]
        try:
            specialization = getattr(profile, specialization_type)
            for key, value in data.items():
                setattr(specialization, key, value)
            specialization.save()
        except AttributeError:
            data['profile'] = profile
            specialization = model_class.objects.create(**data)
        return specialization

    def update(self, instance, validated_data):
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
        instance.update_profile_completion()
        return instance