from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker
from .talent_specialization_serializers import TalentSpecializationSerializer
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
                from .talent_specialization_serializers import VisualWorkerSerializer
                data['visual_worker'] = VisualWorkerSerializer(profile.visual_worker).data
                
            if hasattr(profile, 'expressive_worker'):
                from .talent_specialization_serializers import ExpressiveWorkerSerializer
                data['expressive_worker'] = ExpressiveWorkerSerializer(profile.expressive_worker).data
                
            if hasattr(profile, 'hybrid_worker'):
                from .talent_specialization_serializers import HybridWorkerSerializer
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
        """Remove a specialization from the talent user"""
        try:
            # Get the talent profile for the current user
            profile = TalentUserProfile.objects.get(user=request.user)
            
            # Get the specialization type to remove
            specialization_type = request.data.get('specialization_type')
            
            if not specialization_type or specialization_type not in ['visual_worker', 'expressive_worker', 'hybrid_worker']:
                return Response(
                    {"error": "Invalid specialization type. Must be one of: visual_worker, expressive_worker, hybrid_worker"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if the specialization exists
            if not hasattr(profile, specialization_type):
                return Response(
                    {"error": f"The {specialization_type} specialization does not exist for this profile."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete the specialization
            specialization = getattr(profile, specialization_type)
            specialization.delete()
            
            # Update profile completion status
            profile.update_profile_completion()
            
            return Response(
                {"message": f"{specialization_type} removed successfully.", "profile_complete": profile.profile_complete},
                status=status.HTTP_200_OK
            )
            
        except TalentUserProfile.DoesNotExist:
            return Response(
                {"error": "Talent profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )