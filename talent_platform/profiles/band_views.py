
from inspect import istraceback
import os
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status 
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, ListAPIView, CreateAPIView, DestroyAPIView
from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from .band_serializers import BandCreateSerializer, BandDetailSerializer, BandInvitationSerializer, BandInvitationUseSerializer, BandListSerializer, BandMembershipSerializer, BandUpdateWithMembersSerializer

from .models import BandInvitation, TalentUserProfile,Band, BandMembership
from rest_framework.permissions import IsAuthenticated, BasePermission
from users .permissions import IsTalentUser
# Band Views

# List band for users
class BandListView(ListAPIView):
    serializer_class = BandListSerializer
    permission_classes = [IsAuthenticated,IsTalentUser]
    
    def get_queryset(self):
        # Get the authenticated user's talent profile
        try:
            talent_profile = TalentUserProfile.objects.get(user=self.request.user)
            # Filter bands where the user is a member
            # Optimize queryset to avoid N+1 query problems
            return Band.objects.filter(members=talent_profile).prefetch_related(
                'bandmembership_set'
            ).select_related('creator', 'creator__user')
        except TalentUserProfile.DoesNotExist:
            # If no talent profile exists, return an empty queryset
            return Band.objects.none()

# Get detailed information about a specific band
class BandDetailView(RetrieveAPIView):
    serializer_class = BandDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        # Optimize queryset to avoid N+1 query problems
        return Band.objects.prefetch_related(
            'bandmembership_set',
            'bandmembership_set__talent_user',
            'bandmembership_set__talent_user__user'
        )
    
    def get_object(self):
        band = super().get_object()
        # Check if the user is a member of the band
        try:
            talent_profile = TalentUserProfile.objects.get(user=self.request.user)
            if not BandMembership.objects.filter(band=band, talent_user=talent_profile).exists():
                raise PermissionDenied("You are not a member of this band.")
            return band
        except TalentUserProfile.DoesNotExist:
            raise PermissionDenied("Talent profile not found.")


# Create a new band
class BandCreateView(CreateAPIView):
    serializer_class = BandCreateSerializer
    permission_classes = [IsAuthenticated, IsTalentUser]

    def perform_create(self, serializer):
        serializer.save()

# Update a band
class BandUpdateView(UpdateAPIView):
    serializer_class = BandUpdateWithMembersSerializer
    permission_classes = [IsAuthenticated, IsTalentUser]
    lookup_field = 'id'
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        # Optimize queryset to avoid N+1 query problems
        return Band.objects.prefetch_related(
            'bandmembership_set',
            'bandmembership_set__talent_user',
            'bandmembership_set__talent_user__user'
        )

    def get_object(self):
        band = super().get_object()
        # Check if the user is the creator of the band
        try:
            talent_profile = TalentUserProfile.objects.get(user=self.request.user)
            if band.creator != talent_profile:
                raise PermissionDenied("Only the band creator can update the band details and manage member roles.")
            return band
        except TalentUserProfile.DoesNotExist:
            raise PermissionDenied("Talent profile not found.")
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)  # Default to partial updates for more flexibility
        instance = self.get_object()
        
        # Handle profile picture upload if provided
        if 'profile_picture' in request.FILES:
            # Delete old profile picture if it exists to avoid storage buildup
            if instance.profile_picture:
                try:
                    if os.path.isfile(instance.profile_picture.path):
                        os.remove(instance.profile_picture.path)
                except Exception as e:
                    # Log error but continue with the update
                    print(f"Error removing old profile picture: {e}")
            
            instance.profile_picture = request.FILES['profile_picture']
            instance.save(update_fields=['profile_picture'])
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return updated band with full member details
        updated_serializer = BandDetailSerializer(instance)
        return Response({
            "message": "Band updated successfully",
            "band": updated_serializer.data
        })

# Delete a band
class BandDeleteView(DestroyAPIView):
    queryset = Band.objects.all()
    permission_classes = [IsAuthenticated, IsTalentUser]
    lookup_field = 'id'

    def get_object(self):
        band = super().get_object()
        # Only the creator can delete the band
        user_profile = TalentUserProfile.objects.get(user=self.request.user)
        if band.creator != user_profile:
            raise PermissionDenied("Only the creator can delete this band.")
        return band

# Join a band
class JoinBandView(APIView):
    permission_classes = [IsAuthenticated, IsTalentUser]

    def post(self, request, band_id, *args, **kwargs):
        # Get the band
        try:
            band = Band.objects.get(id=band_id)
        except Band.DoesNotExist:
            return Response({"error": "Band not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get the user's talent profile
        try:
            talent_profile = TalentUserProfile.objects.get(user=request.user)
        except TalentUserProfile.DoesNotExist:
            return Response({"error": "Talent profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is already a member of the band
        if BandMembership.objects.filter(band=band, talent_user=talent_profile).exists():
            return Response({"error": "You are already a member of this band."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the membership
        position = request.data.get('position', '')
        membership = BandMembership.objects.create(
            band=band,
            talent_user=talent_profile,
            role='member',
            position=position
        )

        serializer = BandMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# Leave a band
class LeaveBandView(APIView):
    permission_classes = [IsAuthenticated, IsTalentUser]

    def delete(self, request, band_id, *args, **kwargs):
        # Get the band
        try:
            band = Band.objects.get(id=band_id)
        except Band.DoesNotExist:
            return Response({"error": "Band not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get the user's talent profile
        try:
            talent_profile = TalentUserProfile.objects.get(user=request.user)
        except TalentUserProfile.DoesNotExist:
            return Response({"error": "Talent profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a member of the band
        try:
            membership = BandMembership.objects.get(band=band, talent_user=talent_profile)
        except BandMembership.DoesNotExist:
            return Response({"error": "You are not a member of this band."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is the creator (creators can't leave their own band)
        if band.creator == talent_profile:
            return Response({"error": "As the creator, you cannot leave the band. You must delete it instead."}, status=status.HTTP_400_BAD_REQUEST)

        # Delete the membership
        membership.delete()
        return Response({"message": "You have left the band."}, status=status.HTTP_204_NO_CONTENT)

# Member role updates are now handled through the BandUpdateView with BandUpdateWithMembersSerializer



# Members can only be added through invitation system now


# Generate invitation code for a band (admin only)
class GenerateBandInvitationView(APIView):
    permission_classes = [IsAuthenticated, IsTalentUser]
    
    def post(self, request, band_id, *args, **kwargs):
        # Get the band
        try:
            band = Band.objects.get(id=band_id)
        except Band.DoesNotExist:
            return Response({"error": "Band not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the user's talent profile
        try:
            talent_profile = TalentUserProfile.objects.get(user=request.user)
        except TalentUserProfile.DoesNotExist:
            return Response({"error": "Talent profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the user is an admin of the band
        is_creator = band.creator == talent_profile
        is_admin = BandMembership.objects.filter(band=band, talent_user=talent_profile, role='admin').exists()
        
        # Ensure only creators and admins can generate invitation codes (not regular members)
        if not (is_creator or is_admin):
            return Response({"error": "Only band admins can generate invitation codes."}, status=status.HTTP_403_FORBIDDEN)
        
        # Get position from request data (optional)
        position = request.data.get('position', '')
        
        # Create a new invitation with 15-minute expiration
        from django.utils import timezone
        from datetime import timedelta
        
        invitation = BandInvitation.objects.create(
            band=band,
            created_by=talent_profile,
            position=position,
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        
        serializer = BandInvitationSerializer(invitation)
        return Response({
            "message": f"Invitation code generated successfully. Valid for 15 minutes until {invitation.expires_at.strftime('%H:%M:%S')}.",
            "invitation": serializer.data
        }, status=status.HTTP_201_CREATED)


# List all invitations for a band (admin only)
class BandInvitationsListView(APIView):
    permission_classes = [IsAuthenticated, IsTalentUser]
    
    def get(self, request, band_id, *args, **kwargs):
        # Get the band
        try:
            band = Band.objects.get(id=band_id)
        except Band.DoesNotExist:
            return Response({"error": "Band not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the user's talent profile
        try:
            talent_profile = TalentUserProfile.objects.get(user=request.user)
        except TalentUserProfile.DoesNotExist:
            return Response({"error": "Talent profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the user is an admin of the band
        is_creator = band.creator == talent_profile
        is_admin = BandMembership.objects.filter(band=band, talent_user=talent_profile, role='admin').exists()
        
        if not (is_creator or is_admin):
            return Response({"error": "Only band admins can view invitation codes."}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all invitations for the band with optimized query
        invitations = BandInvitation.objects.filter(band=band).select_related(
            'band', 'created_by', 'created_by__user', 'used_by', 'used_by__user'
        ).order_by('-created_at')
        
        serializer = BandInvitationSerializer(invitations, many=True)
        
        # Add time remaining information for each invitation
        from django.utils import timezone
        invitation_data = serializer.data
        for i, invitation in enumerate(invitations):
            time_remaining = None
            if not invitation.is_used and invitation.expires_at > timezone.now():
                # Calculate time remaining in seconds
                time_remaining = (invitation.expires_at - timezone.now()).total_seconds()
                invitation_data[i]['time_remaining_seconds'] = int(time_remaining)
                invitation_data[i]['time_remaining_formatted'] = f"{int(time_remaining // 60)}m {int(time_remaining % 60)}s"
            else:
                invitation_data[i]['time_remaining_seconds'] = 0
                invitation_data[i]['time_remaining_formatted'] = "Expired"
        
        return Response(invitation_data)


# Use an invitation code to automatically join a band
class UseBandInvitationView(APIView):
    permission_classes = [IsAuthenticated, IsTalentUser]
    
    def post(self, request, *args, **kwargs):
        # Get the user's talent profile
        try:
            talent_profile = TalentUserProfile.objects.get(user=request.user)
        except TalentUserProfile.DoesNotExist:
            return Response({"error": "Talent profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate the invitation code
        serializer = BandInvitationUseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the validated invitation
        invitation = serializer.validated_data['invitation']
        
        # Explicitly check if the invitation has expired
        from django.utils import timezone
        if invitation.expires_at <= timezone.now():
            return Response({
                "error": "This invitation code has expired.",
                "expired_at": invitation.expires_at
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the user is already a member of the band
        if BandMembership.objects.filter(band=invitation.band, talent_user=talent_profile).exists():
            return Response({"error": "You are already a member of this band."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Directly create the membership instead of creating a pending request
            membership = BandMembership.objects.create(
                band=invitation.band,
                talent_user=talent_profile,
                role='member',
                position=invitation.position
            )
            
            # Mark the invitation as used and approved
            invitation.is_used = True
            invitation.used_by = talent_profile
            invitation.status = 'approved'  # Mark as approved since we're automatically adding the user
            invitation.save()
            
            # Return success message with membership details
            membership_serializer = BandMembershipSerializer(membership)
            return Response({
                "message": f"You have successfully joined {invitation.band.name}!",
                "membership": membership_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Note: The following views were documented in band_api_documentation.md but not used in any URL patterns
# They have been removed as part of code cleanup since member management is now handled through
# the BandUpdateView with BandUpdateWithMembersSerializer


