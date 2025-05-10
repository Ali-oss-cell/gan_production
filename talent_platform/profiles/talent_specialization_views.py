from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import (
    TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker
)
from .talent_specialization_serializers import (
    TalentSpecializationSerializer, VisualWorkerSerializer,
    ExpressiveWorkerSerializer, HybridWorkerSerializer
)
from users.permissions import IsTalentUser

class TalentSpecializationView(APIView):
    """View for managing talent specializations"""
    permission_classes = [IsAuthenticated, IsTalentUser]
    
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
            
            return Response(data, status=status.HTTP_200_OK)
            
        except TalentUserProfile.DoesNotExist:
            return Response(
                {"error": "Talent profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        """Create or update specializations for the talent user"""
        try:
            # Get the talent profile for the current user
            profile = TalentUserProfile.objects.get(user=request.user)
            
            # Validate and process the specialization data
            serializer = TalentSpecializationSerializer(data=request.data)
            
            if serializer.is_valid():
                # Update the profile with specializations
                serializer.update(profile, serializer.validated_data)
                
                # Return success response
                return Response(
                    {"message": "Specializations updated successfully.", "profile_complete": profile.profile_complete},
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
                'eye_colors': getattr(ExpressiveWorker, 'EYE_COLORS', []),
                'body_types': getattr(ExpressiveWorker, 'BODY_TYPES', []),
                'union_status': getattr(ExpressiveWorker, 'UNION_STATUS', []),
                'availability': getattr(ExpressiveWorker, 'AVAILABILITY_CHOICES', []),
            })
        
        elif data_type == 'hybrid_worker':
            return Response({
                'hybrid_types': getattr(HybridWorker, 'HYBRID_TYPES', []),
                'hair_colors': getattr(HybridWorker, 'HAIR_COLORS', []),
                'eye_colors': getattr(HybridWorker, 'EYE_COLORS', []),
                'skin_tones': getattr(HybridWorker, 'SKIN_TONES', []),
                'body_types': getattr(HybridWorker, 'BODY_TYPES', []),
                'fitness_levels': getattr(HybridWorker, 'FITNESS_LEVELS', []),
                'risk_levels': getattr(HybridWorker, 'RISK_LEVELS', []),
            })
        
        else:
            return Response({})