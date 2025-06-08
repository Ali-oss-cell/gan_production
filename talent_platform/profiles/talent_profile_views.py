import os
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status 
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, ListAPIView, CreateAPIView, DestroyAPIView
from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from .models import TalentMedia, TalentUserProfile, SocialMediaLinks
from .talent_profile_serializers import TalentMediaSerializer, TalentUserProfileSerializer, SocialMediaLinksSerializer, TalentUserProfileUpdateSerializer
from rest_framework.permissions import IsAuthenticated, BasePermission
from users .permissions import IsTalentUser
from .utils.file_validators import get_max_file_sizes


# Combined view for fetching and updating TalentUserProfile
class TalentUserProfileView(APIView):
    queryset = TalentUserProfile.objects.select_related('user').prefetch_related('social_media_links', 'media').all()
    permission_classes = [IsAuthenticated, IsTalentUser]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_object(self):
        # Fetch the profile of the currently authenticated user
        profile = self.queryset.filter(user=self.request.user).first()
        if not profile:
            raise Http404("Profile not found. Please create your profile first.")
        return profile

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = TalentUserProfileSerializer(profile)
        
        # Get prefetched data
        social_links = getattr(profile, 'social_media_links', None)
        social_data = SocialMediaLinksSerializer(social_links).data if social_links else {}
        
        media = profile.media.all()
        media_serializer = TalentMediaSerializer(media, many=True)
        
        # Combine all data
        response_data = serializer.data
        response_data['social_media_links'] = social_data
        response_data['media'] = media_serializer.data
        
        # Add file upload limits for frontend validation
        response_data['file_limits'] = get_max_file_sizes()
        
        return Response(response_data)
    
    def post(self, request, *args, **kwargs):
        # Handle both full and partial updates through the same method
        # The partial parameter determines if it's a partial update
        partial = request.query_params.get('partial', 'true').lower() == 'true'
        return self.update_profile(request, *args, partial=partial, **kwargs)
    
    def update_profile(self, request, *args, partial=False, **kwargs):
        instance = self.get_object()
        serializer = TalentUserProfileUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'profile': TalentUserProfileSerializer(instance).data
        })

















#great media for talentprofile 
class TalentMediaCreateView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [IsAuthenticated,IsTalentUser]

    def post(self, request, *args, **kwargs):
        # Get the currently authenticated user
        user = request.user 

        # Get the TalentUserProfile associated with the user
        try:
            talent_profile = TalentUserProfile.objects.get(user=user)
        except TalentUserProfile.DoesNotExist:
            return Response({"error": "Talent profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create a new data dictionary without copying the file object
        data = {
            'talent': talent_profile.id,
            'media_file': request.FILES.get('media_file'),  # Get file from request.FILES
            'name': request.data.get('name', ''),  # Get other fields from request.data
            'media_info': request.data.get('media_info', '')
        }

        # Validate and save the data
        serializer = TalentMediaSerializer(data=data)
        if serializer.is_valid():
            # Check account limits before saving
            media_type = 'image' if data['media_file'].content_type.startswith('image/') else 'video'
            
            # Validate against account limits
            if media_type == 'image' and not talent_profile.can_upload_image():
                # Get current count of images
                current_image_count = talent_profile.media.filter(media_type='image', is_test_video=False).count()
                # Get max allowed for account type
                max_images = talent_profile.get_image_limit()
                
                return Response(
                    {
                        "error": f"Upload limit reached for your {talent_profile.account_type.upper()} account.",
                        "details": f"Your {talent_profile.account_type} account allows {max_images} images. You already have {current_image_count} images.",
                        "account_type": talent_profile.account_type,
                        "upgrade_message": "Upgrade your account to upload more media."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif media_type == 'video' and not talent_profile.can_upload_video():
                # Get current count of videos
                current_video_count = talent_profile.media.filter(media_type='video', is_test_video=False).count()
                # Get max allowed for account type
                max_videos = talent_profile.get_video_limit()
                
                return Response(
                    {
                        "error": f"Upload limit reached for your {talent_profile.account_type.upper()} account.",
                        "details": f"Your {talent_profile.account_type} account allows {max_videos} videos. You already have {current_video_count} videos.",
                        "account_type": talent_profile.account_type,
                        "upgrade_message": "Upgrade your account to upload more media."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                # Set media_type based on file content type
                media = serializer.save(media_type=media_type)
                response_data = serializer.data
                response_data['file_limits'] = get_max_file_sizes()
                return Response(response_data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
 
class TalentMediaDeleteView(APIView):
    permission_classes = [IsAuthenticated,IsTalentUser]
    def delete(self, request, media_id, *args, **kwargs):
        # Get the media object
        media = get_object_or_404(TalentMedia, id=media_id)

        # Ensure the user owns the media
        if media.talent.user != request.user:
            return Response(
                {"error": "You do not have permission to delete this media."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Delete the file from the filesystem
        if media.media_file:
            if os.path.isfile(media.media_file.path):
                os.remove(media.media_file.path)

        # Delete the database record
        media.delete()
        return Response(
            {"message": "Media deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

    


    
# Fetch talent links 
class TalentUserLinks(RetrieveAPIView):
    queryset=SocialMediaLinks.objects.all()
    serializer_class=SocialMediaLinksSerializer
    lookup_field = 'user__username'


# Create/Update social media links
class SocialMediaLinksUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsTalentUser]
    parser_classes = [JSONParser]

    def get_object(self):
        """Get or create social media links for the current user"""
        try:
            talent_profile = TalentUserProfile.objects.get(user=self.request.user)
            social_links, created = SocialMediaLinks.objects.get_or_create(user=talent_profile)
            return social_links
        except TalentUserProfile.DoesNotExist:
            raise Http404("Talent profile not found.")

    def get(self, request, *args, **kwargs):
        """Get current social media links"""
        social_links = self.get_object()
        serializer = SocialMediaLinksSerializer(social_links)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Create or update social media links"""
        social_links = self.get_object()
        
        # Update only the fields provided in the request
        allowed_fields = ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'snapchat']
        updated_fields = []
        
        for field in allowed_fields:
            if field in request.data:
                # Validate URL format if provided
                url = request.data[field]
                if url and url.strip():
                    # Basic URL validation
                    if not (url.startswith('http://') or url.startswith('https://')):
                        return Response(
                            {"error": f"Invalid {field} URL format. URLs must start with http:// or https://"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    setattr(social_links, field, url.strip())
                else:
                    # If empty string or None, clear the field
                    setattr(social_links, field, None)
                updated_fields.append(field)
        
        if not updated_fields:
            return Response(
                {"error": "No valid social media fields provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            social_links.save(update_fields=updated_fields)
            
            # Return updated data
            serializer = SocialMediaLinksSerializer(social_links)
            return Response({
                'message': f'Social media links updated successfully. Updated: {", ".join(updated_fields)}',
                'social_media_links': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to update social media links: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

