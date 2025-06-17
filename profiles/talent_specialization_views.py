from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import json

from .models import (
    TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker, TalentMedia
)
from .talent_specialization_serializers import (
    TalentSpecializationSerializer, VisualWorkerSerializer,
    ExpressiveWorkerSerializer, HybridWorkerSerializer
)
from users.permissions import IsTalentUser
from .talent_profile_serializers import TalentMediaSerializer
from .utils.file_validators import get_max_file_sizes

class TalentSpecializationView(APIView):
    """View for managing talent specializations"""
    permission_classes = [IsAuthenticated, IsTalentUser]
    
    def parse_multipart_data(self, request):
        """
        Parse multipart form data into nested structure for the serializer.
        Handles both JSON data and file uploads.
        """
        data = {}
        
        # Parse JSON fields from form data
        for field in ['expressive_worker', 'visual_worker', 'hybrid_worker', 'test_videos', 'about_yourself_video', 'test_images']:
            if field in request.data:
                try:
                    data[field] = json.loads(request.data[field])
                except (json.JSONDecodeError, TypeError):
                    # If it's not JSON, keep as is
                    data[field] = request.data[field]
        
        # Handle file uploads - map files to the media_file fields
        if 'test_videos' in data and isinstance(data['test_videos'], list):
            for i, video_data in enumerate(data['test_videos']):
                file_key = f'test_video_{i + 1}'
                if file_key in request.FILES:
                    video_data['media_file'] = request.FILES[file_key]
        
        if 'about_yourself_video' in data:
            if 'about_video' in request.FILES:
                data['about_yourself_video']['media_file'] = request.FILES['about_video']

        # Handle file uploads for test_images
        if 'test_images' in data and isinstance(data['test_images'], list):
            for i, image_data in enumerate(data['test_images']):
                file_key = f'test_image_{i + 1}' # Assuming files are named test_image_1, test_image_2, etc.
                if file_key in request.FILES:
                    image_data['media_file'] = request.FILES[file_key]

        # Handle image uploads for each specialization
        for spec in ['visual_worker', 'expressive_worker', 'hybrid_worker']:
            if spec in data and isinstance(data[spec], dict):
                for img_field in ['face_picture', 'mid_range_picture', 'full_body_picture']:
                    file_key = f"{spec}_{img_field}"
                    if file_key in request.FILES:
                        data[spec][img_field] = request.FILES[file_key]
        
        return data
    
    def get(self, request):
        """Get the current specializations for the talent user"""
        try:
            # Get the talent profile for the current user
            profile = TalentUserProfile.objects.get(user=request.user)
            
            # Prepare data for response
            data = {}
            
            # Check if user has each specialization and include it if present
            if hasattr(profile, 'visual_worker'):
                data['visual_worker'] = VisualWorkerSerializer(profile.visual_worker).data
                
            if hasattr(profile, 'expressive_worker'):
                data['expressive_worker'] = ExpressiveWorkerSerializer(profile.expressive_worker).data
                
            if hasattr(profile, 'hybrid_worker'):
                data['hybrid_worker'] = HybridWorkerSerializer(profile.hybrid_worker).data
            
            # Include profile completion status
            data['profile_complete'] = profile.profile_complete
            
            # Add file upload limits for frontend validation
            data['file_limits'] = get_max_file_sizes()
            
            return Response(data, status=status.HTTP_200_OK)
            
        except TalentUserProfile.DoesNotExist:
            return Response(
                {"error": "Talent profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        """Create or update specializations for the talent user"""
        try:
            profile = TalentUserProfile.objects.get(user=request.user)
            
            # Parse the request data (handles both JSON and multipart)
            if request.content_type and 'multipart/form-data' in request.content_type:
                parsed_data = self.parse_multipart_data(request)
            else:
                parsed_data = request.data
            
            serializer = TalentSpecializationSerializer(data=parsed_data)
            if serializer.is_valid():
                validated = serializer.validated_data
                # Update the profile with specializations
                serializer.update(profile, validated)
                # Handle test videos and about_yourself_video
                expressive = validated.get('expressive_worker')
                visual = validated.get('visual_worker')
                hybrid = validated.get('hybrid_worker')
                test_videos = validated.get('test_videos', [])
                about_yourself_video = validated.get('about_yourself_video', None)
                
                # Check if any specialization is being created/updated
                has_specialization = any([expressive, visual, hybrid])
                performer_type = expressive.get('performer_type') if expressive else None
                
                errors = []
                created_videos = []
                
                if has_specialization:
                    # Save the 4 test videos (only for actor, comparse, host)
                    if performer_type in ['actor', 'comparse', 'host'] and test_videos:
                        for vid in test_videos:
                            vid_data = {
                                'talent': profile.id,
                                'media_file': vid['media_file'],
                                'name': vid.get('name', ''),
                                'media_info': vid.get('media_info', ''),
                                'is_test_video': True,
                                'is_about_yourself_video': False,
                                'test_video_number': vid['test_video_number']
                            }
                            media_serializer = TalentMediaSerializer(data=vid_data)
                            if media_serializer.is_valid():
                                try:
                                    media_type = 'video'
                                    media_serializer.save(media_type=media_type)
                                    created_videos.append(media_serializer.data)
                                except Exception as e:
                                    errors.append(str(e))
                            else:
                                errors.append(media_serializer.errors)
                    
                    # Save the about_yourself_video (required for ALL specializations)
                    if about_yourself_video:
                        about_data = {
                            'talent': profile.id,
                            'media_file': about_yourself_video['media_file'],
                            'name': about_yourself_video.get('name', 'About Yourself'),
                            'media_info': about_yourself_video.get('media_info', 'Talk about yourself'),
                            'is_test_video': True,
                            'is_about_yourself_video': True,
                            'test_video_number': 5
                        }
                        about_serializer = TalentMediaSerializer(data=about_data)
                        if about_serializer.is_valid():
                            try:
                                media_type = 'video'
                                about_serializer.save(media_type=media_type)
                                created_videos.append(about_serializer.data)
                            except Exception as e:
                                errors.append(str(e))
                        else:
                            errors.append(about_serializer.errors)
                
                if errors:
                    return Response({'error': 'Some test videos failed to upload.', 'details': errors}, status=status.HTTP_400_BAD_REQUEST)
                return Response(
                    {
                        "message": "Specializations updated successfully.", 
                        "profile_complete": profile.profile_complete, 
                        "test_videos": created_videos,
                        "file_limits": get_max_file_sizes()
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TalentUserProfile.DoesNotExist:
            return Response(
                {"error": "Talent profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request):
        """Remove a specialization from a talent profile"""
        try:
            profile = TalentUserProfile.objects.get(user=request.user)
            specialization = request.query_params.get('specialization')
            
            if not specialization or specialization not in ['visual_worker', 'expressive_worker', 'hybrid_worker']:
                return Response(
                    {"error": "Valid specialization parameter required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if hasattr(profile, specialization):
                # Get the specialization instance
                spec_instance = getattr(profile, specialization)
                # Delete it
                spec_instance.delete()
                # Update profile completion
                profile.update_profile_completion()
                
                return Response(
                    {"message": f"{specialization.replace('_', ' ').title()} specialization removed successfully.",
                     "profile_complete": profile.profile_complete},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": f"This profile doesn't have a {specialization.replace('_', ' ')} specialization."},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except TalentUserProfile.DoesNotExist:
            return Response(
                {"error": "Talent profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class ReferenceDataView(APIView):
    """View for getting reference data for forms"""
    
    def get(self, request):
        data_type = request.query_params.get('type')
        
        if data_type == 'visual_worker':
            return Response({
                'primary_categories': getattr(VisualWorker, 'PRIMARY_CATEGORIES', []),
                'experience_levels': getattr(VisualWorker, 'EXPERIENCE_LEVEL', []),
                'availability_choices': getattr(VisualWorker, 'AVAILABILITY_CHOICES', []),
                'rate_ranges': getattr(VisualWorker, 'RATE_RANGES', []),
            })
        
        elif data_type == 'expressive_worker':
            return Response({
                'performer_types': getattr(ExpressiveWorker, 'PERFORMER_TYPES', []),
                'hair_colors': getattr(ExpressiveWorker, 'HAIR_COLORS', []),
                'hair_types': getattr(ExpressiveWorker, 'HAIR_TYPES', []),
                'skin_tones': getattr(ExpressiveWorker, 'SKIN_TONES', []),
                'eye_colors': getattr(ExpressiveWorker, 'EYE_COLORS', []),
                'eye_sizes': getattr(ExpressiveWorker, 'EYE_SIZES', []),
                'eye_patterns': getattr(ExpressiveWorker, 'EYE_PATTERNS', []),
                'face_shapes': getattr(ExpressiveWorker, 'FACE_SHAPES', []),
                'forehead_shapes': getattr(ExpressiveWorker, 'FOREHEAD_SHAPES', []),
                'lip_shapes': getattr(ExpressiveWorker, 'LIP_SHAPES', []),
                'eyebrow_patterns': getattr(ExpressiveWorker, 'EYEBROW_PATTERNS', []),
                'beard_colors': getattr(ExpressiveWorker, 'BEARD_COLORS', []),
                'beard_lengths': getattr(ExpressiveWorker, 'BEARD_LENGTHS', []),
                'mustache_colors': getattr(ExpressiveWorker, 'HAIR_COLORS', []),
                'mustache_lengths': getattr(ExpressiveWorker, 'BEARD_LENGTHS', []),
                'distinctive_facial_marks': getattr(ExpressiveWorker, 'FACIAL_MARKS', []),
                'distinctive_body_marks': getattr(ExpressiveWorker, 'BODY_MARKS', []),
                'voice_types': getattr(ExpressiveWorker, 'VOICE_TYPES', []),
                'body_types': getattr(ExpressiveWorker, 'BODY_TYPES', []),
                'union_status': getattr(ExpressiveWorker, 'UNION_STATUS', []),
                'availability': getattr(ExpressiveWorker, 'AVAILABILITY_CHOICES', []),
            })
        
        elif data_type == 'hybrid_worker':
            return Response({
                'hybrid_types': getattr(HybridWorker, 'HYBRID_TYPES', []),
                'hair_colors': getattr(HybridWorker, 'HAIR_COLORS', []),
                'hair_types': getattr(HybridWorker, 'HAIR_TYPES', []),
                'eye_colors': getattr(HybridWorker, 'EYE_COLORS', []),
                'eye_sizes': getattr(HybridWorker, 'EYE_SIZES', []),
                'eye_patterns': getattr(HybridWorker, 'EYE_PATTERNS', []),
                'face_shapes': getattr(HybridWorker, 'FACE_SHAPES', []),
                'forehead_shapes': getattr(HybridWorker, 'FOREHEAD_SHAPES', []),
                'lip_shapes': getattr(HybridWorker, 'LIP_SHAPES', []),
                'eyebrow_patterns': getattr(HybridWorker, 'EYEBROW_PATTERNS', []),
                'beard_colors': getattr(HybridWorker, 'HAIR_COLORS', []),
                'beard_lengths': getattr(HybridWorker, 'BEARD_LENGTHS', []),
                'mustache_colors': getattr(HybridWorker, 'HAIR_COLORS', []),
                'mustache_lengths': getattr(HybridWorker, 'BEARD_LENGTHS', []),
                'distinctive_facial_marks': getattr(HybridWorker, 'FACIAL_MARKS', []),
                'distinctive_body_marks': getattr(HybridWorker, 'BODY_MARKS', []),
                'voice_types': getattr(HybridWorker, 'VOICE_TYPES', []),
                'skin_tones': getattr(HybridWorker, 'SKIN_TONES', []),
                'body_types': getattr(HybridWorker, 'BODY_TYPES', []),
                'fitness_levels': getattr(HybridWorker, 'FITNESS_LEVELS', []),
                'risk_levels': getattr(HybridWorker, 'RISK_LEVELS', []),
                'availability_choices': getattr(HybridWorker, 'AVAILABILITY_CHOICES', []),
            })
        
        else:
            return Response({})