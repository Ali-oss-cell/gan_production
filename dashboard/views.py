from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework.permissions import IsAdminUser
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from django.urls import reverse

from users.models import BaseUser
from users.serializers import UnifiedUserSerializer
from users.permissions import IsAdminDashboardUser, IsDashboardUser
from profiles.models import TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker, TalentMedia, Band, BackGroundJobsProfile
from .serializers import (
    TalentDashboardSerializer, VisualWorkerDashboardSerializer, 
    ExpressiveWorkerDashboardSerializer, HybridWorkerDashboardSerializer,
    BandDashboardSerializer, BackGroundDashboardSerializer
)
from .utils import get_sharing_status
from profiles.utils.media_url_helper import get_media_url, get_thumbnail_url




class DashboardUserCreateView(APIView):
    """View for creating new dashboard users"""
    permission_classes = [IsAdminDashboardUser]
    
    def post(self, request):
        """Create a new dashboard user"""
        data = request.data.copy()
        data['role'] = 'dashboard'
        
        serializer = UnifiedUserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Dashboard user created successfully',
                'id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Failed to create dashboard user',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DashboardUserManagementView(APIView):
    """View for admin dashboard users to manage regular dashboard users"""
    permission_classes = [IsAdminDashboardUser]
    
    def get(self, request):
        """List all dashboard users"""
        dashboard_users = BaseUser.objects.filter(is_dashboard=True)
        # Exclude admin users if requested
        if request.query_params.get('exclude_admins') == 'true':
            dashboard_users = dashboard_users.filter(is_staff=False)
            
        user_data = [{
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            
            'is_active': user.is_active
        } for user in dashboard_users]
        
        return Response(user_data, status=status.HTTP_200_OK)


class DashboardUserDetailView(APIView):
    """View for admin dashboard users to manage a specific dashboard user"""
    permission_classes = [IsAdminDashboardUser]
    
    def get_object(self, pk):
        try:
            user = BaseUser.objects.get(pk=pk, is_dashboard=True)
            return user
        except BaseUser.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        """Get details of a specific dashboard user"""
        user = self.get_object(pk)
        data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined,
            'is_active': user.is_active
        }
        return Response(data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        """Delete a dashboard user"""
        user = self.get_object(pk)
        # Prevent admin users from deleting themselves
        if user.id == request.user.id:
            return Response({
                'message': 'You cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        # Prevent deleting other admin users
        if user.is_staff and user.id != request.user.id:
            return Response({
                'message': 'You cannot delete other admin users'
            }, status=status.HTTP_403_FORBIDDEN)
            
        user.delete()
        return Response({
            'message': 'Dashboard user deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


# Profile Detail Views for Dashboard Users
class TalentProfileDetailView(RetrieveAPIView):
    """View for dashboard users to see detailed talent profile information"""
    queryset = TalentUserProfile.objects.select_related('user').prefetch_related('media')
    serializer_class = TalentDashboardSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get_sharing_status(self, media):
        """
        Get sharing status for a media item using centralized utility.
        """
        return get_sharing_status(media)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add all media items associated with this profile with sharing status
        media_items = instance.media.all()
        data['media_items'] = []
        for media in media_items:
            # Get sharing status using centralized utility
            sharing_status = self.get_sharing_status(media)
            
            media_data = {
                'id': media.id,
                'name': media.name,
                'media_type': media.media_type,
                'media_info': media.media_info,
                'media_file': get_media_url(request, media.media_file),
                'thumbnail': get_thumbnail_url(request, media.thumbnail),
                'created_at': media.created_at,
                'is_test_video': media.is_test_video,
                'is_about_yourself_video': media.is_about_yourself_video,
                'sharing_status': sharing_status
            }
            data['media_items'].append(media_data)
        
        # Add specialization details
        if hasattr(instance, 'visual_worker'):
            data['visual_worker'] = VisualWorkerDashboardSerializer(instance.visual_worker).data
        
        if hasattr(instance, 'expressive_worker'):
            data['expressive_worker'] = ExpressiveWorkerDashboardSerializer(instance.expressive_worker).data
            
        if hasattr(instance, 'hybrid_worker'):
            data['hybrid_worker'] = HybridWorkerDashboardSerializer(instance.hybrid_worker).data
        
        # Record profile view or other analytics here if needed
        
        return Response(data)


class BackGroundJobsProfileDetailView(RetrieveAPIView):
    """View for dashboard users to see detailed background profile information"""
    queryset = BackGroundJobsProfile.objects.select_related('user').prefetch_related(
        'prop_items', 'costume_items', 'location_items', 'memorabilia_items',
        'vehicle_items', 'artisticmaterial_items', 'musicitem_items', 'rareitem_items'
    )
    serializer_class = BackGroundDashboardSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add all items associated with this background profile
        data['items'] = {
            'props': [],
            'costumes': [],
            'locations': [],
            'memorabilia': [],
            'vehicles': [],
            'artistic_materials': [],
            'music_items': [],
            'rare_items': []
        }
        
        # Add props
        for prop in instance.prop_items.all():
            prop_data = {
                'id': prop.id,
                'name': prop.name,
                'description': prop.description,
                'price': prop.price,
                'material': prop.material,
                'used_in_movie': prop.used_in_movie,
                'condition': prop.condition,
                'is_for_rent': prop.is_for_rent,
                'is_for_sale': prop.is_for_sale,
                'image': request.build_absolute_uri(prop.image.url) if prop.image else None,
                'created_at': prop.created_at,
                'updated_at': prop.updated_at
            }
            data['items']['props'].append(prop_data)
        
        # Add costumes
        for costume in instance.costume_items.all():
            costume_data = {
                'id': costume.id,
                'name': costume.name,
                'description': costume.description,
                'price': costume.price,
                'size': costume.size,
                'worn_by': costume.worn_by,
                'era': costume.era,
                'is_for_rent': costume.is_for_rent,
                'is_for_sale': costume.is_for_sale,
                'image': request.build_absolute_uri(costume.image.url) if costume.image else None,
                'created_at': costume.created_at,
                'updated_at': costume.updated_at
            }
            data['items']['costumes'].append(costume_data)
        
        # Add locations
        for location in instance.location_items.all():
            location_data = {
                'id': location.id,
                'name': location.name,
                'description': location.description,
                'price': location.price,
                'address': location.address,
                'capacity': location.capacity,
                'is_indoor': location.is_indoor,
                'is_for_rent': location.is_for_rent,
                'is_for_sale': location.is_for_sale,
                'image': request.build_absolute_uri(location.image.url) if location.image else None,
                'created_at': location.created_at,
                'updated_at': location.updated_at
            }
            data['items']['locations'].append(location_data)
        
        # Add memorabilia
        for memorabilia in instance.memorabilia_items.all():
            memorabilia_data = {
                'id': memorabilia.id,
                'name': memorabilia.name,
                'description': memorabilia.description,
                'price': memorabilia.price,
                'signed_by': memorabilia.signed_by,
                'authenticity_certificate': request.build_absolute_uri(memorabilia.authenticity_certificate.url) if memorabilia.authenticity_certificate else None,
                'is_for_rent': memorabilia.is_for_rent,
                'is_for_sale': memorabilia.is_for_sale,
                'image': request.build_absolute_uri(memorabilia.image.url) if memorabilia.image else None,
                'created_at': memorabilia.created_at,
                'updated_at': memorabilia.updated_at
            }
            data['items']['memorabilia'].append(memorabilia_data)
        
        # Add vehicles
        for vehicle in instance.vehicle_items.all():
            vehicle_data = {
                'id': vehicle.id,
                'name': vehicle.name,
                'description': vehicle.description,
                'price': vehicle.price,
                'make': vehicle.make,
                'model': vehicle.model,
                'year': vehicle.year,
                'is_for_rent': vehicle.is_for_rent,
                'is_for_sale': vehicle.is_for_sale,
                'image': request.build_absolute_uri(vehicle.image.url) if vehicle.image else None,
                'created_at': vehicle.created_at,
                'updated_at': vehicle.updated_at
            }
            data['items']['vehicles'].append(vehicle_data)
        
        # Add artistic materials
        for artistic_material in instance.artisticmaterial_items.all():
            artistic_material_data = {
                'id': artistic_material.id,
                'name': artistic_material.name,
                'description': artistic_material.description,
                'price': artistic_material.price,
                'type': artistic_material.type,
                'condition': artistic_material.condition,
                'is_for_rent': artistic_material.is_for_rent,
                'is_for_sale': artistic_material.is_for_sale,
                'image': request.build_absolute_uri(artistic_material.image.url) if artistic_material.image else None,
                'created_at': artistic_material.created_at,
                'updated_at': artistic_material.updated_at
            }
            data['items']['artistic_materials'].append(artistic_material_data)
        
        # Add music items
        for music_item in instance.musicitem_items.all():
            music_item_data = {
                'id': music_item.id,
                'name': music_item.name,
                'description': music_item.description,
                'price': music_item.price,
                'instrument_type': music_item.instrument_type,
                'used_by': music_item.used_by,
                'is_for_rent': music_item.is_for_rent,
                'is_for_sale': music_item.is_for_sale,
                'image': request.build_absolute_uri(music_item.image.url) if music_item.image else None,
                'created_at': music_item.created_at,
                'updated_at': music_item.updated_at
            }
            data['items']['music_items'].append(music_item_data)
        
        # Add rare items
        for rare_item in instance.rareitem_items.all():
            rare_item_data = {
                'id': rare_item.id,
                'name': rare_item.name,
                'description': rare_item.description,
                'price': rare_item.price,
                'provenance': rare_item.provenance,
                'is_one_of_a_kind': rare_item.is_one_of_a_kind,
                'is_for_rent': rare_item.is_for_rent,
                'is_for_sale': rare_item.is_for_sale,
                'image': request.build_absolute_uri(rare_item.image.url) if rare_item.image else None,
                'created_at': rare_item.created_at,
                'updated_at': rare_item.updated_at
            }
            data['items']['rare_items'].append(rare_item_data)
        
        return Response(data)


class VisualWorkerDetailView(RetrieveAPIView):
    """View for dashboard users to see detailed visual worker profile information"""
    queryset = VisualWorker.objects.select_related('profile').prefetch_related('profile__media')
    serializer_class = VisualWorkerDashboardSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get_sharing_status(self, media):
        """
        Get sharing status for a media item using centralized utility.
        """
        return get_sharing_status(media)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add all media items associated with this profile with sharing status
        media_items = instance.profile.media.all()
        data['media_items'] = []
        for media in media_items:
            # Get sharing status using centralized utility
            sharing_status = self.get_sharing_status(media)
            
            media_data = {
                'id': media.id,
                'name': media.name,
                'media_type': media.media_type,
                'media_info': media.media_info,
                'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                'created_at': media.created_at,
                'is_test_video': media.is_test_video,
                'is_about_yourself_video': media.is_about_yourself_video,
                'sharing_status': sharing_status
            }
            data['media_items'].append(media_data)
        
        return Response(data)


class ExpressiveWorkerDetailView(RetrieveAPIView):
    """View for dashboard users to see detailed expressive worker profile information"""
    queryset = ExpressiveWorker.objects.select_related('profile').prefetch_related('profile__media')
    serializer_class = ExpressiveWorkerDashboardSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get_sharing_status(self, media):
        """
        Get sharing status for a media item using centralized utility.
        """
        return get_sharing_status(media)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add all media items associated with this profile with sharing status
        media_items = instance.profile.media.all()
        data['media_items'] = []
        for media in media_items:
            # Get sharing status using centralized utility
            sharing_status = self.get_sharing_status(media)
            
            media_data = {
                'id': media.id,
                'name': media.name,
                'media_type': media.media_type,
                'media_info': media.media_info,
                'media_file': get_media_url(request, media.media_file),
                'thumbnail': get_thumbnail_url(request, media.thumbnail),
                'created_at': media.created_at,
                'is_test_video': media.is_test_video,
                'is_about_yourself_video': media.is_about_yourself_video,
                'sharing_status': sharing_status
            }
            data['media_items'].append(media_data)
        
        return Response(data)


class HybridWorkerDetailView(RetrieveAPIView):
    """View for dashboard users to see detailed hybrid worker profile information"""
    queryset = HybridWorker.objects.select_related('profile').prefetch_related('profile__media')
    serializer_class = HybridWorkerDashboardSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add all media items associated with this profile
        media_items = instance.profile.media.all()
        data['media_items'] = [{
            'id': media.id,
            'name': media.name,
            'media_type': media.media_type,
            'media_info': media.media_info,
            'media_file': get_media_url(request, media.media_file),
            'thumbnail': get_thumbnail_url(request, media.thumbnail),
            'created_at': media.created_at,
        } for media in media_items]
        
        return Response(data)


class BandDetailView(RetrieveAPIView):
    """View for dashboard users to see detailed band information"""
    queryset = Band.objects.all().prefetch_related('members', 'media')
    serializer_class = BandDashboardSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add all media items associated with this band
        media_items = instance.media.all()
        data['media_items'] = [{
            'id': media.id,
            'name': media.name,
            'media_type': media.media_type,
            'media_info': media.media_info,
            'media_file': get_media_url(request, media.media_file),
            'created_at': media.created_at,
        } for media in media_items]
        
        # Add URLs for band members' profiles
        for member in data['members']:
            member['profile_url'] = request.build_absolute_uri(
                reverse('dashboard:talent-profile-detail', args=[member['profile_id']])
            ) if member['profile_id'] else None
        
        return Response(data)


class AllProfilesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class AllProfilesView(ListAPIView):
    """View that aggregates all talent profiles in one page for dashboard users"""
    serializer_class = TalentDashboardSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    pagination_class = AllProfilesPagination
    
    def get_queryset(self):
        # Get base queryset of all talent profiles
        return TalentUserProfile.objects.all().prefetch_related('media')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Apply filtering if requested
        profile_type = request.query_params.get('profile_type', None)
        
        # Filter by specialization type if requested
        visual_profiles = []
        expressive_profiles = []
        hybrid_profiles = []
        
        if profile_type == 'visual' or profile_type is None:
            visual_profiles = queryset.filter(visual_worker__isnull=False)
            
        if profile_type == 'expressive' or profile_type is None:
            expressive_profiles = queryset.filter(expressive_worker__isnull=False)
            
        if profile_type == 'hybrid' or profile_type is None:
            hybrid_profiles = queryset.filter(hybrid_worker__isnull=False)
        
        # Combine querysets if needed
        if profile_type is None:
            combined_queryset = queryset
        else:
            if profile_type == 'visual':
                combined_queryset = visual_profiles
            elif profile_type == 'expressive':
                combined_queryset = expressive_profiles
            elif profile_type == 'hybrid':
                combined_queryset = hybrid_profiles
            else:
                combined_queryset = queryset
        
        # Apply pagination
        page = self.paginate_queryset(combined_queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data
            
            # Add links to detailed profile views
            for item in data:
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:talent-profile-detail', args=[item['id']]))
                
                # Check for specializations
                profile = queryset.get(id=item['id'])
                if hasattr(profile, 'visual_worker'):
                    item['visual_worker_url'] = request.build_absolute_uri(
                        reverse('dashboard:visual-worker-detail', args=[profile.visual_worker.id]))
                
                if hasattr(profile, 'expressive_worker'):
                    item['expressive_worker_url'] = request.build_absolute_uri(
                        reverse('dashboard:expressive-worker-detail', args=[profile.expressive_worker.id]))
                
                if hasattr(profile, 'hybrid_worker'):
                    item['hybrid_worker_url'] = request.build_absolute_uri(
                        reverse('dashboard:hybrid-worker-detail', args=[profile.hybrid_worker.id]))
            
            # Add category counts to response
            response_data = {
                'counts': {
                    'total': queryset.count(),
                    'visual': visual_profiles.count(),
                    'expressive': expressive_profiles.count(),
                    'hybrid': hybrid_profiles.count(),
                },
                'active_filter': profile_type or 'all',
            }
            
            return self.get_paginated_response(data)
        
        # If not paginated
        serializer = self.get_serializer(combined_queryset, many=True)
        data = serializer.data
        
        # Add profile URLs
        for item in data:
            item['profile_url'] = request.build_absolute_uri(reverse('dashboard:talent-profile-detail', args=[item['id']]))
        
        return Response(data)
