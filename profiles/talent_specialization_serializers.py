from rest_framework import serializers
from .models import VisualWorker, ExpressiveWorker, HybridWorker, TalentMedia
from .talent_profile_serializers import TalentMediaSerializer

class VisualWorkerSerializer(serializers.ModelSerializer):
    profile = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    face_picture = serializers.ImageField(required=False, allow_null=True)
    mid_range_picture = serializers.ImageField(required=False, allow_null=True)
    full_body_picture = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = VisualWorker
        fields = [
            'id', 'profile', 'primary_category', 'years_experience', 'experience_level',
            'portfolio_link', 'availability', 'rate_range', 'willing_to_relocate',
            'created_at', 'updated_at',
            'face_picture', 'mid_range_picture', 'full_body_picture'
        ]
        read_only_fields = ['id', 'profile', 'created_at', 'updated_at']

class ExpressiveWorkerSerializer(serializers.ModelSerializer):
    profile = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    face_picture = serializers.ImageField(required=False, allow_null=True)
    mid_range_picture = serializers.ImageField(required=False, allow_null=True)
    full_body_picture = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = ExpressiveWorker
        fields = [
            'id', 'profile', 'performer_type', 'years_experience', 'height', 'weight',
            'hair_color', 'hair_type', 'skin_tone', 'eye_color', 'eye_size', 'eye_pattern',
            'face_shape', 'forehead_shape', 'lip_shape', 'eyebrow_pattern',
            'beard_color', 'beard_length', 'mustache_color', 'mustache_length',
            'distinctive_facial_marks', 'distinctive_body_marks', 'voice_type',
            'body_type', 'availability',
            'created_at', 'updated_at',
            'face_picture', 'mid_range_picture', 'full_body_picture'
        ]
        read_only_fields = ['id', 'profile', 'created_at', 'updated_at']

class HybridWorkerSerializer(serializers.ModelSerializer):
    profile = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    face_picture = serializers.ImageField(required=False, allow_null=True)
    mid_range_picture = serializers.ImageField(required=False, allow_null=True)
    full_body_picture = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = HybridWorker
        fields = [
            'id', 'profile', 'hybrid_type', 'years_experience', 'height', 'weight',
            'hair_color', 'hair_type',
            'eye_color', 'eye_size', 'eye_pattern',
            'face_shape', 'forehead_shape', 'lip_shape', 'eyebrow_pattern',
            'beard_color', 'beard_length', 'mustache_color', 'mustache_length',
            'distinctive_facial_marks', 'distinctive_body_marks',
            'voice_type',
            'skin_tone', 'body_type',
            'fitness_level', 'risk_levels', 'availability',
            'willing_to_relocate', 'created_at', 'updated_at',
            'face_picture', 'mid_range_picture', 'full_body_picture'
        ]
        read_only_fields = ['id', 'profile', 'created_at', 'updated_at']

class TalentSpecializationSerializer(serializers.Serializer):
    visual_worker = VisualWorkerSerializer(required=False)
    expressive_worker = ExpressiveWorkerSerializer(required=False)
    hybrid_worker = HybridWorkerSerializer(required=False)
    # Accept test_videos as a list of dicts (for actor/comparse)
    test_videos = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=True
    )
    # New: about_yourself_video as a separate dict
    about_yourself_video = serializers.DictField(required=False)
    # New: test_images field for up to 4 test images
    test_images = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=True, write_only=True
    )

    def validate(self, data):
        if not any([data.get('visual_worker'), data.get('expressive_worker'), data.get('hybrid_worker')]):
            raise serializers.ValidationError("At least one specialization (Visual Worker, Expressive Worker, or Hybrid Worker) must be provided.")

        expressive_data = data.get('expressive_worker')
        visual_data = data.get('visual_worker') # Retained for clarity, not directly used in media logic
        hybrid_data = data.get('hybrid_worker') # Retained for clarity

        test_videos_input = data.get('test_videos', [])
        test_images_input = data.get('test_images', [])
        about_yourself_video_input = data.get('about_yourself_video', None)

        # 1. About Yourself Video Validation (Required for any specialization)
        if not about_yourself_video_input:
            raise serializers.ValidationError({'about_yourself_video': 'You must upload the 1-minute about yourself video.'})
        if not about_yourself_video_input.get('is_test_video', False):
            raise serializers.ValidationError({'about_yourself_video': 'About yourself video must be marked as a test video (is_test_video=True).'})
        if not about_yourself_video_input.get('is_about_yourself_video', False):
            raise serializers.ValidationError({'about_yourself_video': 'About yourself video must be marked as is_about_yourself_video=True.'})
        
        about_video_num_str = about_yourself_video_input.get('test_video_number')
        try:
            about_video_num = int(about_video_num_str)
            if about_video_num != 5:
                raise ValueError("About yourself video number must be 5.")
        except (ValueError, TypeError):
            raise serializers.ValidationError({'about_yourself_video': 'About yourself video must have test_video_number 5 (as an integer).'})

        if 'media_file' not in about_yourself_video_input or not about_yourself_video_input['media_file']:
            raise serializers.ValidationError({'about_yourself_video': 'About yourself video must include a media_file.'})

        # 2. Test Videos and Test Images Validation (Depends on specialization type)
        if expressive_data:
            performer_type = expressive_data.get('performer_type')
            if performer_type in ['actor', 'comparse', 'host']:
                # Test Videos: 4 required for these performer types
                if len(test_videos_input) != 4:
                    raise serializers.ValidationError({'test_videos': f'You must upload exactly 4 test videos (numbered 1-4) for {performer_type} roles.'})
                seen_video_numbers = set()
                for i, vid_data in enumerate(test_videos_input):
                    if not vid_data.get('is_test_video', False):
                        raise serializers.ValidationError({'test_videos': f'Test video #{i+1} must be marked as is_test_video=True.'})
                    num_vid_str = vid_data.get('test_video_number')
                    try:
                        num_vid_int = int(num_vid_str)
                        if not (1 <= num_vid_int <= 4):
                            raise ValueError('Test video number out of range 1-4.')
                    except (ValueError, TypeError):
                        raise serializers.ValidationError({'test_videos': f'Test video #{i+1} must have a valid integer test_video_number between 1 and 4.'})
                    if num_vid_int in seen_video_numbers:
                        raise serializers.ValidationError({'test_videos': f'Duplicate test_video_number: {num_vid_int}. Numbers must be unique (1-4).'})
                    seen_video_numbers.add(num_vid_int)
                    if 'media_file' not in vid_data or not vid_data['media_file']:
                        raise serializers.ValidationError({'test_videos': f'Test video #{i+1} (number {num_vid_int}) must include a media_file.'})

                # Test Images: 4 required for these performer types
                if len(test_images_input) != 4:
                    raise serializers.ValidationError({'test_images': f'You must upload exactly 4 test images (numbered 1-4) for {performer_type} roles.'})
                seen_image_numbers = set()
                for i, img_data in enumerate(test_images_input):
                    if not img_data.get('is_test_image', False):
                        raise serializers.ValidationError({'test_images': f'Test image #{i+1} must be marked as is_test_image=True.'})
                    num_img_str = img_data.get('test_image_number')
                    try:
                        num_img_int = int(num_img_str)
                        if not (1 <= num_img_int <= 4):
                            raise ValueError('Test image number out of range 1-4.')
                    except (ValueError, TypeError):
                        raise serializers.ValidationError({'test_images': f'Test image #{i+1} must have a valid integer test_image_number between 1 and 4.'})
                    if num_img_int in seen_image_numbers:
                        raise serializers.ValidationError({'test_images': f'Duplicate test_image_number: {num_img_int}. Numbers must be unique (1-4).'})
                    seen_image_numbers.add(num_img_int)
                    if 'media_file' not in img_data or not img_data['media_file']:
                        raise serializers.ValidationError({'test_images': f'Test image #{i+1} (number {num_img_int}) must include a media_file.'})
            else:
                # Other ExpressiveWorker types: NO test_videos or test_images allowed
                if test_videos_input:
                    raise serializers.ValidationError({'test_videos': f'Test videos are only for actor, comparse, or host roles, not for ExpressiveWorker type: {performer_type}. Please remove them.'})
                if test_images_input:
                    raise serializers.ValidationError({'test_images': f'Test images are only for actor, comparse, or host roles, not for ExpressiveWorker type: {performer_type}. Please remove them.'})
        else:
            # VisualWorker or HybridWorker: NO test_videos or test_images allowed
            worker_category = "VisualWorker" if visual_data else "HybridWorker" if hybrid_data else "Non-Expressive role"
            if test_videos_input:
                raise serializers.ValidationError({'test_videos': f'Test videos are only for ExpressiveWorker (actor, comparse, host). Not allowed for {worker_category}. Please remove them.'})
            if test_images_input:
                raise serializers.ValidationError({'test_images': f'Test images are only for ExpressiveWorker (actor, comparse, host). Not allowed for {worker_category}. Please remove them.'})
            
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
            # Create a new instance without explicitly setting city/country
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