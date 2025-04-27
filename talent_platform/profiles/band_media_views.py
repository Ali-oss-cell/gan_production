import os
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from .models import BandMedia, Band, BandMembership, TalentUserProfile
from .band_media_serializers import BandMediaSerializer
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsTalentUser
from .permissions import IsBandAdmin


class BandMediaView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [IsAuthenticated, IsTalentUser]
    
    def get(self, request, band_id, *args, **kwargs):
        """
        List all media for a specific band
        """
        # Get the band
        band = get_object_or_404(Band, id=band_id)
        
        # Check if the user is a member of the band
        try:
            talent_profile = TalentUserProfile.objects.get(user=request.user)
            if not BandMembership.objects.filter(band=band, talent_user=talent_profile).exists():
                return Response({"error": "You are not a member of this band."}, status=status.HTTP_403_FORBIDDEN)
        except TalentUserProfile.DoesNotExist:
            return Response({"error": "Talent profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all media for the band
        media = band.media.all()
        serializer = BandMediaSerializer(media, many=True)
        
        return Response(serializer.data)
    
    def post(self, request, band_id, *args, **kwargs):
        """
        Upload media for a specific band (admin only)
        """
        # Get the band
        band = get_object_or_404(Band, id=band_id)
        
        # Check if the user is an admin of the band
        try:
            talent_profile = TalentUserProfile.objects.get(user=request.user)
            is_admin = BandMembership.objects.filter(band=band, talent_user=talent_profile, role='admin').exists()
            is_creator = band.creator == talent_profile
            
            if not (is_admin or is_creator):
                return Response({"error": "Only band admins can upload media."}, status=status.HTTP_403_FORBIDDEN)
        except TalentUserProfile.DoesNotExist:
            return Response({"error": "Talent profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Create a new data dictionary with the band ID
        data = {
            'band': band.id,
            'media_file': request.FILES.get('media_file'),  # Get file from request.FILES
            'name': request.data.get('name', 'Untitled Media'),  # Get other fields from request.data
            'media_info': request.data.get('media_info', '')
        }
        
        # Validate and save the data
        serializer = BandMediaSerializer(data=data)
        if serializer.is_valid():
            try:
                # The media_type will be set automatically in the serializer's validate method
                media = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BandMediaDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsTalentUser, IsBandAdmin]
    
    def delete(self, request, band_id, media_id, *args, **kwargs):
        """
        Delete a specific media item from a band (admin only)
        """
        # Get the band and media
        band = get_object_or_404(Band, id=band_id)
        media = get_object_or_404(BandMedia, id=media_id, band=band)
        
        # Check if the user is an admin of the band (handled by IsBandAdmin permission)
        
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