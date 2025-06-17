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

from .background_serializers import BackGroundJobs,PropSerializer,CostumeSerializer,LocationSerializer,MemorabiliaSerializer,VehicleSerializer,MusicItemSerializer,RareItemSerializer,ArtisticMaterialSerializer
from .background_serializers import ItemSerializer
from .models import BackGroundJobsProfile, Prop, Costume, Location, Memorabilia, Vehicle, ArtisticMaterial, MusicItem, RareItem
from rest_framework.permissions import IsAuthenticated, BasePermission
from users .permissions import IsBackgroundUser



class BackGroundJobsUserProfileDetailView(RetrieveAPIView):
    queryset = BackGroundJobsProfile.objects.all()
    serializer_class = BackGroundJobs
    permission_classes = [IsAuthenticated,IsBackgroundUser]
    lookup_field = 'id'  # Use the primary key (id) of TalentUserProfile

    def get_object(self):
        # Fetch the profile of the currently authenticated user
        profile = self.queryset.filter(user=self.request.user).first()
        if not profile:
            raise Http404("Profile not found. Please create your profile first.")
        return profile
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to include profile score"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Get the profile score
        score_data = instance.get_profile_score()
        
        # Return profile data with score
        return Response({
            'profile': serializer.data,
            'profile_score': score_data
        })




class GreatItems(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated,IsBackgroundUser]  # Only authenticated users can access this view
    
    def get_serializer_class(self, item_type):
        # Map item types to their respective serializers
        serializer_map = {
            'prop': PropSerializer,
            'costume': CostumeSerializer,
            'location': LocationSerializer,
            'memorabilia': MemorabiliaSerializer,
            'vehicle': VehicleSerializer,
            'artistic_material': ArtisticMaterialSerializer,
            'music_item': MusicItemSerializer,
            'rare_item': RareItemSerializer,
        }
        return serializer_map.get(item_type, ItemSerializer)  # Default to ItemSerializer if type not found
        
    def get_model_for_item_type(self, item_type):
        # Map item types to their respective models
        model_map = {
            'prop': Prop,
            'costume': Costume,
            'location': Location,
            'memorabilia': Memorabilia,
            'vehicle': Vehicle,
            'artistic_material': ArtisticMaterial,
            'music_item': MusicItem,
            'rare_item': RareItem,
        }
        return model_map.get(item_type, Prop)  # Default to Prop if type not found

    def post(self, request, *args, **kwargs):
        user = request.user

        # Get the backgroundjobsporfile associated with the user
        try:
            backgroundjobs_profile = BackGroundJobsProfile.objects.get(user=user)
        except BackGroundJobsProfile.DoesNotExist:
            return Response({"error": "Back GroundJobs profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Determine the type of item being uploaded
        item_type = request.data.get('item_type')  # Assuming 'item_type' is passed in the request data

        # Get the appropriate serializer class based on the item type
        serializer_class = self.get_serializer_class(item_type)
        
        # Get the appropriate model for the item type
        model = self.get_model_for_item_type(item_type)

        # Validate and save the item
        serializer = serializer_class(data=request.data, context={'request': request, 'model': model})
        if serializer.is_valid():
            # Save with the background profile
            serializer.save(BackGroundJobsProfile=backgroundjobs_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)