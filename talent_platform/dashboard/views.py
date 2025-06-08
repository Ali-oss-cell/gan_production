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
from profiles.models import TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker, TalentMedia, Band
from .serializers import (
    TalentDashboardSerializer, VisualWorkerDashboardSerializer, 
    ExpressiveWorkerDashboardSerializer, HybridWorkerDashboardSerializer,
    BandDashboardSerializer
)




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
            'date_joined': user.date_joined,
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
    queryset = TalentUserProfile.objects.all().prefetch_related('media')
    serializer_class = TalentDashboardSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add all media items associated with this profile
        media_items = instance.media.all()
        data['media_items'] = [{
            'id': media.id,
            'name': media.name,
            'media_type': media.media_type,
            'media_info': media.media_info,
            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
            'created_at': media.created_at,
        } for media in media_items]
        
        # Add specialization details
        if hasattr(instance, 'visual_worker'):
            data['visual_worker'] = VisualWorkerDashboardSerializer(instance.visual_worker).data
        
        if hasattr(instance, 'expressive_worker'):
            data['expressive_worker'] = ExpressiveWorkerDashboardSerializer(instance.expressive_worker).data
            
        if hasattr(instance, 'hybrid_worker'):
            data['hybrid_worker'] = HybridWorkerDashboardSerializer(instance.hybrid_worker).data
        
        # Record profile view or other analytics here if needed
        
        return Response(data)


class VisualWorkerDetailView(RetrieveAPIView):
    """View for dashboard users to see detailed visual worker profile information"""
    queryset = VisualWorker.objects.select_related('profile').prefetch_related('profile__media')
    serializer_class = VisualWorkerDashboardSerializer
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
            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
            'created_at': media.created_at,
        } for media in media_items]
        
        return Response(data)


class ExpressiveWorkerDetailView(RetrieveAPIView):
    """View for dashboard users to see detailed expressive worker profile information"""
    queryset = ExpressiveWorker.objects.select_related('profile').prefetch_related('profile__media')
    serializer_class = ExpressiveWorkerDashboardSerializer
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
            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
            'created_at': media.created_at,
        } for media in media_items]
        
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
            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
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
            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
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
