from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType

from users.permissions import IsDashboardUser, IsAdminDashboardUser
from .models import SharedMediaPost
from .serializers import (
    ShareMediaSerializer, 
    SharedMediaPostSerializer,
    SharedMediaPostListSerializer
)


class ShareMediaView(APIView):
    """
    API endpoint for dashboard admins to share media from search results.
    Note: Original media owner information is kept private for privacy and business purposes.
    Companies interested in the media should contact the dashboard for connections.
    
    POST /api/dashboard/share-media/
    {
        "content_type": "talent_media",  // or band_media, prop, costume, etc.
        "object_id": 123,
        "caption": "Amazing work by our talent!",
        "category": "featured",  // optional
        "attribution": " Talent Platform"  // optional, defaults to dashboard name
    }

    Response:
    {
        "message": "Media shared successfully!",
        "shared_post": {
            "id": 1,
            "content_type": "talent_media",
            "object_id": 123,
            "caption": "Amazing work by our talent!",
            "category": "featured",
            "shared_by": {
                "id": 1,
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User"
            },
            "attribution": "Talent Platform",
            "shared_at": "2024-03-21T10:00:00Z",
            "is_active": true
        }
    }

    Error Responses:
    - 400 Bad Request: Invalid data or media already shared
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not a dashboard user
    - 404 Not Found: Media object not found
    - 500 Internal Server Error: Server error
    """
    permission_classes = [IsAuthenticated, IsDashboardUser | IsAdminDashboardUser]
    
    def post(self, request):
        # Log the incoming request
        print("=== SHARE MEDIA REQUEST ===")
        print(f"User: {request.user.id}")
        print(f"Request data: {request.data}")
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        
        serializer = ShareMediaSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            print("✅ Serializer is valid")
            try:
                # Get the content type and object
                content_type_name = serializer.validated_data['content_type']
                object_id = serializer.validated_data['object_id']
                
                print(f"Looking for content_type={content_type_name}, object_id={object_id}")
                
                # Fix: Split the content_type_name like the serializer does
                app_label, model_name = content_type_name.split('.')
                content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
                print(f"Found content_type: {content_type}")
                
                media_object = content_type.get_object_for_this_type(id=object_id)
                print(f"Found media_object: {media_object}")
                
                # Create the shared post - we don't expose the original owner
                shared_post = serializer.save()
                print(f"Created shared_post: {shared_post.id}")
                
                response_serializer = SharedMediaPostSerializer(shared_post)
                
                return Response({
                    'message': 'Media shared successfully!',
                    'shared_post': response_serializer.data
                }, status=status.HTTP_201_CREATED)
                
            except IntegrityError as e:
                print(f"❌ IntegrityError: {str(e)}")
                # Check if this media is already shared by any admin
                try:
                    existing_share = SharedMediaPost.objects.get(
                        content_type=content_type,
                        object_id=object_id,
                        is_active=True
                    )
                    return Response({
                        'error': 'This media is already shared in the gallery',
                        'existing_share_id': existing_share.id,
                        'shared_by': {
                            'id': existing_share.shared_by.id,
                            'name': f"{existing_share.shared_by.first_name} {existing_share.shared_by.last_name}".strip() or existing_share.shared_by.email
                        },
                        'shared_at': existing_share.shared_at,
                        'suggestion': 'You can contact the admin who shared it or wait for it to be removed'
                    }, status=status.HTTP_400_BAD_REQUEST)
                except SharedMediaPost.DoesNotExist:
                    return Response({
                        'error': 'Unable to share this media. Please try again.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except ContentType.DoesNotExist as e:
                print(f"❌ ContentType.DoesNotExist: {str(e)}")
                return Response({
                    'error': f'Invalid content type: {content_type_name}'
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return Response({
                    'error': f'Failed to share media: {str(e)}',
                    'details': 'Please check the server logs for more information'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print(f"❌ Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SharedMediaListView(generics.ListAPIView):
    """
    API endpoint to list shared media for gallery display.
    Note: Original media owner information is kept private.
    Companies interested in the media should contact the dashboard for connections.
    
    GET /api/dashboard/shared-media/
    
    PUBLIC ACCESS: Anyone can view the gallery (for landing page)
    
    Query parameters:
    - category: Filter by category (featured, inspiration, trending, etc.)
    - shared_by: Filter by who shared it (user ID)
    - content_type: Filter by content type (talent_media, band_media, etc.)
    - limit: Number of results per page
    
    Response:
    {
        "count": 10,
        "next": "next_page_url",
        "previous": "previous_page_url",
        "results": [
            {
                "id": 1,
                "content_type": "talent_media",
                "object_id": 123,
                "caption": "Amazing work!",
                "category": "featured",
                "shared_by": {
                    "id": 1,
                    "email": "admin@example.com",
                    "first_name": "Admin",
                    "last_name": "User"
                },
                "attribution": "Talent Platform",
                "shared_at": "2024-03-21T10:00:00Z",
                "is_active": true
            }
        ]
    }
    """
    serializer_class = SharedMediaPostListSerializer
    permission_classes = []  # Allow anonymous access for public gallery
    
    def get_queryset(self):
        queryset = SharedMediaPost.objects.filter(is_active=True).select_related(
            'shared_by', 'content_type'
        )
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by who shared it
        shared_by = self.request.query_params.get('shared_by')
        if shared_by:
            queryset = queryset.filter(shared_by_id=shared_by)
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type__model=content_type)
        
        return queryset


class SharedMediaDetailView(generics.RetrieveAPIView):
    """
    API endpoint to get detailed info about a specific shared media post.
    Note: Original media owner information is kept private.
    Companies interested in the media should contact the dashboard for connections.
    
    GET /api/dashboard/shared-media/{id}/
    
    PUBLIC ACCESS: Anyone can view individual shared posts
    
    Response:
    {
        "id": 1,
        "content_type": "talent_media",
        "object_id": 123,
        "caption": "Amazing work!",
        "category": "featured",
        "shared_by": {
            "id": 1,
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User"
        },
        "attribution": "Talent Platform",
        "shared_at": "2024-03-21T10:00:00Z",
        "is_active": true,
        "media_details": {
            // Additional media-specific details based on content_type
        }
    }
    """
    queryset = SharedMediaPost.objects.filter(is_active=True)
    serializer_class = SharedMediaPostSerializer
    permission_classes = []  # Allow anonymous access for public viewing


class DeleteSharedMediaView(APIView):
    """
    API endpoint for dashboard admins to delete their shared media posts.
    
    DELETE /api/dashboard/shared-media/{id}/
    
    Response:
    {
        "message": "Shared media deleted successfully"
    }
    
    Error Responses:
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not authorized to delete this post
    - 404 Not Found: Post not found
    """
    permission_classes = [IsAuthenticated, IsDashboardUser | IsAdminDashboardUser]
    
    def delete(self, request, pk):
        shared_post = get_object_or_404(SharedMediaPost, pk=pk, is_active=True)
        
        # Check permissions - users can only delete their own shares, or admins can delete any
        if not (shared_post.shared_by == request.user or request.user.is_dashboard_admin):
            return Response({
                'error': 'You can only delete your own shared posts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Soft delete - just mark as inactive
        shared_post.is_active = False
        shared_post.save()
        
        return Response({
            'message': 'Shared media deleted successfully'
        }, status=status.HTTP_200_OK)


class MySharedMediaView(generics.ListAPIView):
    """
    API endpoint for dashboard users to see their own shared media.
    
    GET /api/dashboard/my-shared-media/
    
    Response:
    {
        "count": 10,
        "next": "next_page_url",
        "previous": "previous_page_url",
        "results": [
            {
                "id": 1,
                "content_type": "talent_media",
                "object_id": 123,
                "caption": "Amazing work!",
                "category": "featured",
                "attribution": "Talent Platform",
                "shared_at": "2024-03-21T10:00:00Z",
                "is_active": true
            }
        ]
    }
    """
    serializer_class = SharedMediaPostSerializer
    permission_classes = [IsAuthenticated, IsDashboardUser | IsAdminDashboardUser]
    
    def get_queryset(self):
        return SharedMediaPost.objects.filter(
            shared_by=self.request.user,
            is_active=True
        ).select_related('shared_by', 'content_type').order_by('-shared_at')


class UpdateSharedMediaView(APIView):
    """
    API endpoint for dashboard users to update shared media posts.
    Since only one admin can share each media, any admin can update any shared media.
    
    PUT /api/dashboard/shared-media/{id}/update/
    
    Request Body:
    {
        "caption": "Updated caption",
        "category": "featured"
    }
    
    Response:
    {
        "message": "Shared media updated successfully!",
        "shared_post": {
            "id": 1,
            "caption": "Updated caption",
            "category": "featured",
            "shared_at": "2024-03-21T10:00:00Z"
        }
    }
    """
    permission_classes = [IsAuthenticated, IsDashboardUser | IsAdminDashboardUser]
    
    def put(self, request, pk):
        try:
            shared_post = SharedMediaPost.objects.get(
                pk=pk, 
                is_active=True
            )
        except SharedMediaPost.DoesNotExist:
            return Response({
                'error': 'Shared media not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update fields
        if 'caption' in request.data:
            shared_post.caption = request.data['caption']
        if 'category' in request.data:
            shared_post.category = request.data['category']
        
        shared_post.save()
        
        response_serializer = SharedMediaPostSerializer(shared_post)
        
        return Response({
            'message': 'Shared media updated successfully!',
            'shared_post': response_serializer.data
        }, status=status.HTTP_200_OK)


class SharedMediaStatsView(APIView):
    """
    API endpoint to get statistics about shared media.
    Note: Original media owner information is kept private in public stats.
    
    GET /api/dashboard/shared-media/stats/
    
    Response:
    {
        "total_shared": 100,
        "by_category": {
            "featured": 50,
            "inspiration": 30,
            "trending": 20
        },
        "by_content_type": {
            "talent_media": 60,
            "band_media": 30,
            "prop": 10
        },
        "top_sharers": [
            {
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@example.com",
                "count": 25
            }
        ]
    }
    """
    permission_classes = [IsAuthenticated, IsAdminDashboardUser]
    
    def get(self, request):
        from django.db.models import Count
        
        stats = {
            'total_shared': SharedMediaPost.objects.filter(is_active=True).count(),
            'by_category': dict(
                SharedMediaPost.objects.filter(is_active=True)
                .values('category')
                .annotate(count=Count('id'))
                .values_list('category', 'count')
            ),
            'by_content_type': dict(
                SharedMediaPost.objects.filter(is_active=True)
                .values('content_type__model')
                .annotate(count=Count('id'))
                .values_list('content_type__model', 'count')
            ),
            'top_sharers': list(
                SharedMediaPost.objects.filter(is_active=True)
                .values('shared_by__first_name', 'shared_by__last_name', 'shared_by__email')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
        }
        
        return Response(stats) 