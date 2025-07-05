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
from .utils.subscription_checker import check_background_user_subscription, get_background_user_restrictions
from payments.models import Subscription
from payments.serializers import SubscriptionSerializer



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
        """Override retrieve to include profile score and subscription status"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Get the profile score
        score_data = instance.get_profile_score()
        
        # Get subscription status and restrictions
        subscription_check = check_background_user_subscription(request.user)
        restrictions = get_background_user_restrictions(request.user)
        
        # Get active subscription details if exists
        subscription_data = None
        if subscription_check['has_subscription']:
            subscription = subscription_check['subscription']
            subscription_data = SubscriptionSerializer(subscription).data
        
        # Return profile data with score, subscription status, and restrictions
        return Response({
            'profile': serializer.data,
            'profile_score': score_data,
            'subscription_status': {
                'has_subscription': subscription_check['has_subscription'],
                'can_access_features': subscription_check['can_access_features'],
                'message': subscription_check['message'],
                'subscription': subscription_data
            },
            'restrictions': restrictions
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

        # Check subscription status for background users
        subscription_check = check_background_user_subscription(user)
        if not subscription_check['can_access_features']:
            return Response({
                'error': 'Subscription required',
                'message': subscription_check['message'],
                'restrictions': get_background_user_restrictions(user)
            }, status=status.HTTP_403_FORBIDDEN)

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

    def get(self, request, *args, **kwargs):
        """Get items for background user - allows viewing even without subscription"""
        user = request.user

        # Get the backgroundjobsporfile associated with the user
        try:
            backgroundjobs_profile = BackGroundJobsProfile.objects.get(user=user)
        except BackGroundJobsProfile.DoesNotExist:
            return Response({"error": "Back GroundJobs profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get item type from query params (optional)
        item_type = request.query_params.get('item_type')
        
        # Get subscription status for additional info
        subscription_check = check_background_user_subscription(user)
        
        if item_type:
            # Get specific item type
            model = self.get_model_for_item_type(item_type)
            items = model.objects.filter(BackGroundJobsProfile=backgroundjobs_profile)
            serializer_class = self.get_serializer_class(item_type)
        else:
            # Get all items grouped by type
            all_items = {}
            for item_type_name in ['prop', 'costume', 'location', 'memorabilia', 'vehicle', 'artistic_material', 'music_item', 'rare_item']:
                model = self.get_model_for_item_type(item_type_name)
                items = model.objects.filter(BackGroundJobsProfile=backgroundjobs_profile)
                serializer_class = self.get_serializer_class(item_type_name)
                serialized_items = serializer_class(items, many=True).data
                all_items[item_type_name] = serialized_items
            
            return Response({
                'items': all_items,
                'subscription_status': {
                    'has_subscription': subscription_check['has_subscription'],
                    'can_access_features': subscription_check['can_access_features'],
                    'message': subscription_check['message']
                },
                'total_items': sum(len(items) for items in all_items.values())
            })

        # Serialize items
        serializer = serializer_class(items, many=True)
        
        return Response({
            'items': serializer.data,
            'item_type': item_type,
            'subscription_status': {
                'has_subscription': subscription_check['has_subscription'],
                'can_access_features': subscription_check['can_access_features'],
                'message': subscription_check['message']
            },
            'total_items': items.count()
        })

class BackgroundUserSubscriptionStatusView(APIView):
    """
    API endpoint for background users to check their subscription status
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get subscription status for background user"""
        user = request.user
        
        # Check if user is a background user
        if not hasattr(user, 'is_background') or not user.is_background:
            return Response({
                'error': 'This endpoint is only for background users'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get subscription status
        subscription_check = check_background_user_subscription(user)
        restrictions = get_background_user_restrictions(user)
        
        # Get active subscription details if exists
        subscription_data = None
        if subscription_check['has_subscription']:
            subscription = subscription_check['subscription']
            subscription_data = SubscriptionSerializer(subscription).data
        
        return Response({
            'has_subscription': subscription_check['has_subscription'],
            'can_access_features': subscription_check['can_access_features'],
            'message': subscription_check['message'],
            'subscription': subscription_data,
            'restrictions': restrictions
        })

class BackgroundUserRestrictionsView(APIView):
    """
    API endpoint to get restrictions for background users without subscription
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get restrictions for background user"""
        user = request.user
        
        # Check if user is a background user
        if not hasattr(user, 'is_background') or not user.is_background:
            return Response({
                'error': 'This endpoint is only for background users'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restrictions = get_background_user_restrictions(user)
        
        return Response(restrictions)

class BackgroundItemDetailView(APIView):
    """
    API endpoint for getting, updating, and deleting individual background items
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsBackgroundUser]
    
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
        return serializer_map.get(item_type, ItemSerializer)
        
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
        return model_map.get(item_type, Prop)
    
    def get(self, request, item_type, item_id):
        """Get a specific item by ID - allows viewing even without subscription"""
        user = request.user
        
        # Get the background profile
        try:
            backgroundjobs_profile = BackGroundJobsProfile.objects.get(user=user)
        except BackGroundJobsProfile.DoesNotExist:
            return Response({"error": "Back GroundJobs profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the item
        model = self.get_model_for_item_type(item_type)
        try:
            item = model.objects.get(id=item_id, BackGroundJobsProfile=backgroundjobs_profile)
        except model.DoesNotExist:
            return Response({"error": f"{item_type.title()} not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize the item
        serializer_class = self.get_serializer_class(item_type)
        serializer = serializer_class(item)
        
        # Get subscription status
        subscription_check = check_background_user_subscription(user)
        
        return Response({
            'item': serializer.data,
            'item_type': item_type,
            'subscription_status': {
                'has_subscription': subscription_check['has_subscription'],
                'can_access_features': subscription_check['can_access_features'],
                'message': subscription_check['message']
            }
        })
    
    def put(self, request, item_type, item_id):
        """Update an item - requires subscription"""
        user = request.user
        
        # Check subscription status
        subscription_check = check_background_user_subscription(user)
        if not subscription_check['can_access_features']:
            return Response({
                'error': 'Subscription required',
                'message': subscription_check['message'],
                'restrictions': get_background_user_restrictions(user)
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the background profile
        try:
            backgroundjobs_profile = BackGroundJobsProfile.objects.get(user=user)
        except BackGroundJobsProfile.DoesNotExist:
            return Response({"error": "Back GroundJobs profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the item
        model = self.get_model_for_item_type(item_type)
        try:
            item = model.objects.get(id=item_id, BackGroundJobsProfile=backgroundjobs_profile)
        except model.DoesNotExist:
            return Response({"error": f"{item_type.title()} not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Update the item
        serializer_class = self.get_serializer_class(item_type)
        serializer = serializer_class(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, item_type, item_id):
        """Delete an item - requires subscription"""
        user = request.user
        
        # Check subscription status
        subscription_check = check_background_user_subscription(user)
        if not subscription_check['can_access_features']:
            return Response({
                'error': 'Subscription required',
                'message': subscription_check['message'],
                'restrictions': get_background_user_restrictions(user)
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the background profile
        try:
            backgroundjobs_profile = BackGroundJobsProfile.objects.get(user=user)
        except BackGroundJobsProfile.DoesNotExist:
            return Response({"error": "Back GroundJobs profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the item
        model = self.get_model_for_item_type(item_type)
        try:
            item = model.objects.get(id=item_id, BackGroundJobsProfile=backgroundjobs_profile)
        except model.DoesNotExist:
            return Response({"error": f"{item_type.title()} not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete the item
        item.delete()
        return Response({"message": f"{item_type.title()} deleted successfully."}, status=status.HTTP_204_NO_CONTENT)