from rest_framework import generics, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from django.db.models import Q, F, ExpressionWrapper, FloatField, Count, Case, When, Value, IntegerField, CharField
from django.db.models.functions import Coalesce, Concat
from django.utils import timezone
from datetime import datetime, date, timedelta
import math
from django.contrib.contenttypes.models import ContentType

from users.permissions import IsDashboardUser, IsAdminDashboardUser

# Import models
from profiles.models import (
    TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker, 
    BackGroundJobsProfile, Band,
    Prop, Costume, Location, Memorabilia, Vehicle, 
    ArtisticMaterial, MusicItem, RareItem
)

# Import serializers
from .serializers import (
    TalentDashboardSerializer, VisualWorkerDashboardSerializer, 
    ExpressiveWorkerDashboardSerializer, HybridWorkerDashboardSerializer,
    BackGroundDashboardSerializer, BandDashboardSerializer,
    PropDashboardSerializer, CostumeDashboardSerializer, LocationDashboardSerializer, 
    MemorabilaDashboardSerializer, VehicleDashboardSerializer,
    ArtisticMaterialDashboardSerializer, MusicItemDashboardSerializer, 
    RareItemDashboardSerializer
)

# Import filters
from .filters import (
    TalentUserProfileFilter, VisualWorkerFilter, ExpressiveWorkerFilter, 
    HybridWorkerFilter, BackGroundJobsProfileFilter, BandFilter,
    PropFilter, CostumeFilter, LocationFilter, MemorabiliaFilter, 
    VehicleFilter, ArtisticMaterialFilter, MusicItemFilter, RareItemFilter
)

# Import shared media post model
from .models import SharedMediaPost

# Define a common mixin for all search views
class SearchViewMixin:
    """Mixin with common attributes for all search views"""
    format_kwarg = 'format'
    
    def get_sharing_status(self, media):
        """
        Get sharing status for a media item using centralized utility.
        Returns sharing information if the media is already shared.
        Guarantees to always return a valid sharing status object.
        """
        from .utils import get_sharing_status
        return get_sharing_status(media)
    
    def calculate_simple_relevance_score(self, item, query_params, field_mappings):
        """
        Simple relevance scoring based on field matches.
        
        Args:
            item: The model instance
            query_params: Request query parameters
            field_mappings: Dict mapping query param names to model field names and weights
                Example: {'name': ('name', 20), 'city': ('city', 15)}
        
        Returns:
            int: Relevance score (0-100)
        """
        score = 0
        
        for param_name, (field_name, weight) in field_mappings.items():
            if param_name in query_params and query_params[param_name]:
                field_value = getattr(item, field_name, None)
                if field_value:
                    if isinstance(field_value, str):
                        if query_params[param_name].lower() in field_value.lower():
                            score += weight
                    elif field_value == query_params[param_name]:
                        score += weight
        
        return min(score, 100)  # Cap at 100

class TalentUserProfileSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = TalentUserProfile.objects.all().prefetch_related('media')
    serializer_class = TalentDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TalentUserProfileFilter
    ordering_fields = ['date_of_birth', 'created_at', 'city', 'country', 'account_type']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get_queryset(self):
        """
        Optimized queryset with annotations to reduce database queries
        """
        return TalentUserProfile.objects.select_related(
            'user'
        ).prefetch_related(
            'media',
            'visual_worker',
            'expressive_worker', 
            'hybrid_worker'
        ).annotate(
            # Annotate media counts to avoid N+1 queries
            image_count=Count('media', filter=Q(media__media_type='image', media__is_test_video=False)),
            video_count=Count('media', filter=Q(media__media_type='video', media__is_test_video=False)),
            total_media=Count('media', filter=Q(media__is_test_video=False)),
            # Annotate age calculation
            age=Case(
                When(
                    date_of_birth__isnull=False,
                    then=timezone.now().year - F('date_of_birth__year') - 
                         Case(
                             When(
                                 Q(date_of_birth__month__gt=timezone.now().month) |
                                 Q(date_of_birth__month=timezone.now().month, date_of_birth__day__gt=timezone.now().day),
                                 then=Value(1)
                             ),
                             default=Value(0)
                         )
                ),
                default=Value(None),
                output_field=IntegerField()
            ),
            # Annotate specialization count
            specialization_count=Case(
                When(visual_worker__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            ) + Case(
                When(expressive_worker__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            ) + Case(
                When(hybrid_worker__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        )
    
    def calculate_relevance_score(self, queryset, filters):
        """
        Calculate a relevance score for each result based on how closely it matches the filter criteria
        Higher score = better match
        """
        query_params = self.request.query_params
        
        # Create a list of profiles with their relevance scores
        profiles_with_scores = []
        
        for profile in queryset:
            score = 100  # Start with a perfect score
            
            # Score gender match
            if 'gender' in query_params and profile.gender:
                score += 20 if profile.gender.lower() == query_params['gender'].lower() else 0
            
            # Score city match (partial match can still get points)
            if 'city' in query_params and profile.city:
                if query_params['city'].lower() in profile.city.lower():
                    score += 15
                elif profile.city.lower() in query_params['city'].lower():
                    score += 10
            
            # Score country match
            if 'country' in query_params and profile.country:
                if query_params['country'].lower() in profile.country.lower():
                    score += 15
                elif profile.country.lower() in query_params['country'].lower():
                    score += 10
            
            # Score age match
            if 'age' in query_params and profile.date_of_birth:
                target_age = int(query_params['age'])
                today = datetime.today()
                age = today.year - profile.date_of_birth.year - ((today.month, today.day) < 
                     (profile.date_of_birth.month, profile.date_of_birth.day))
                
                # Calculate score based on how close the age is
                age_diff = abs(age - target_age)
                if age_diff == 0:
                    score += 20
                elif age_diff <= 2:
                    score += 15
                elif age_diff <= 5:
                    score += 10
                elif age_diff <= 10:
                    score += 5
            
            # Score account type match
            if 'account_type' in query_params:
                score += 10 if profile.account_type == query_params['account_type'] else 0
            
            # Score verified profiles higher
            if 'is_verified' in query_params:
                req_verified = query_params['is_verified'].lower() in ('true', '1', 'yes')
                score += 15 if profile.is_verified == req_verified else 0
            elif profile.is_verified:
                # Bonus for verified profiles even if not explicitly requested
                score += 5
            
            # Score profile completion
            if profile.profile_complete:
                score += 10
            
            # Score media count - profiles with more media might be more appealing
            media_count = profile.media.count()
            if media_count > 10:
                score += 15
            elif media_count > 5:
                score += 10
            elif media_count > 0:
                score += 5
                
            # Add premium account bonuses - prioritize paid accounts
            if profile.account_type == 'platinum':
                score += 30  # Highest tier gets biggest bonus
            elif profile.account_type == 'gold':
                score += 20  # Medium tier gets medium bonus
            elif profile.account_type == 'silver':
                score += 10  # Basic paid tier gets small bonus
            # Free accounts get no bonus
            
            profiles_with_scores.append((profile, score))
        
        # Sort by score descending
        profiles_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return the sorted profiles and their scores
        return profiles_with_scores
    
    def calculate_profile_score(self, profile):
        """
        Get the profile score from the model's method.
        """
        score_breakdown = profile.get_profile_score()
        return score_breakdown['total']
    
    def list(self, request, *args, **kwargs):
        # Start with the full queryset
        original_queryset = self.get_queryset()
        
        # Apply filters from filter backends (Django-filter)
        filtered_queryset = self.filter_queryset(original_queryset)
        
        # Apply additional custom filtering for fields that aren't covered by the filter class
        query_params = self.request.query_params
        
        # Skip the default profile_type parameter, it's used for routing
        search_params = {k: v for k, v in query_params.items() if k != 'profile_type' and k != 'format' and k != 'include_media'}
        
        # Check if media should be included
        include_media = query_params.get('include_media', '').lower() in ('true', '1', 'yes')
        
        # Apply explicit filters only if search parameters are provided
        if search_params:
            # Additional strict filtering for fields not directly handled by the filter backend
            if 'gender' in search_params and search_params['gender']:
                filtered_queryset = filtered_queryset.filter(gender__iexact=search_params['gender'])
            
            if 'city' in search_params and search_params['city']:
                filtered_queryset = filtered_queryset.filter(city__icontains=search_params['city'])
            
            if 'country' in search_params and search_params['country']:
                filtered_queryset = filtered_queryset.filter(country__icontains=search_params['country'])
            
            if 'account_type' in search_params and search_params['account_type']:
                filtered_queryset = filtered_queryset.filter(account_type__iexact=search_params['account_type'])
            
            if 'is_verified' in search_params:
                is_verified = search_params['is_verified'].lower() in ('true', '1', 'yes')
                filtered_queryset = filtered_queryset.filter(is_verified=is_verified)
            
            if 'age' in search_params:
                try:
                    target_age = int(search_params['age'])
                    today = datetime.today()
                    # Calculate the date range for the target age
                    start_date = date(today.year - target_age - 1, today.month, today.day) + timedelta(days=1)
                    end_date = date(today.year - target_age, today.month, today.day)
                    filtered_queryset = filtered_queryset.filter(date_of_birth__gte=start_date, date_of_birth__lte=end_date)
                except (ValueError, TypeError):
                    # If age isn't a valid integer, ignore this filter
                    pass
            
            # Filter by specialization type
            if 'specialization' in search_params:
                spec_type = search_params['specialization'].lower()
                if spec_type == 'visual':
                    filtered_queryset = filtered_queryset.filter(visual_worker__isnull=False)
                elif spec_type == 'expressive':
                    filtered_queryset = filtered_queryset.filter(expressive_worker__isnull=False)
                elif spec_type == 'hybrid':
                    filtered_queryset = filtered_queryset.filter(hybrid_worker__isnull=False)
        
        # If filter parameters are applied, calculate relevance score for sorting the filtered results
        if search_params and filtered_queryset.exists():
            profiles_with_scores = self.calculate_relevance_score(filtered_queryset, search_params)
            
            # Extract just the profiles from the scored results
            queryset = [profile for profile, score in profiles_with_scores]
            
            # Paginate
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                # Add relevance scores, profile scores, and profile URLs to the results
                for i, item in enumerate(data):
                    item['relevance_score'] = profiles_with_scores[i][1]
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:talent-profile-detail', args=[item['id']]))
                    
                    # Include media data if requested
                    if include_media:
                        item['media_items'] = []
                        for media in page[i].media.all():
                            # Get sharing status with guaranteed fallback
                            sharing_status = self.get_sharing_status(media)
                            if not sharing_status or not isinstance(sharing_status, dict):
                                sharing_status = {'is_shared': False}
                            
                            media_data = {
                                'id': media.id,
                                'name': media.name,
                                'media_info': media.media_info,
                                'media_type': media.media_type,
                                'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                                'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                                'created_at': media.created_at,
                                'is_test_video': media.is_test_video,
                                'is_about_yourself_video': media.is_about_yourself_video,
                                'sharing_status': sharing_status
                            }
                            item['media_items'].append(media_data)
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            # Add relevance scores, profile scores, and profile URLs to the results
            for i, item in enumerate(data):
                item['relevance_score'] = profiles_with_scores[i][1]
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:talent-profile-detail', args=[item['id']]))
                
                # Include media data if requested
                if include_media:
                    item['media_items'] = []
                    for media in queryset[i].media.all():
                        # Get sharing status with guaranteed fallback
                        sharing_status = self.get_sharing_status(media)
                        if not sharing_status or not isinstance(sharing_status, dict):
                            sharing_status = {'is_shared': False}
                        
                        media_data = {
                            'id': media.id,
                            'name': media.name,
                            'media_info': media.media_info,
                            'media_type': media.media_type,
                            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                            'created_at': media.created_at,
                            'is_test_video': media.is_test_video,
                            'is_about_yourself_video': media.is_about_yourself_video,
                            'sharing_status': sharing_status
                        }
                        item['media_items'].append(media_data)
            
            return Response(data)
        else:
            # No valid filters applied or no results after filtering
            if search_params and not filtered_queryset.exists():
                return Response({"message": "No profiles match your search criteria."}, status=200)
            
            # If no search criteria, return the default sorted results
            page = self.paginate_queryset(filtered_queryset.order_by('-id'))
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                for i, item in enumerate(data):
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:talent-profile-detail', args=[item['id']]))
                    
                    # Include media data if requested
                    if include_media:
                        item['media_items'] = []
                        for media in page[i].media.all():
                            # Get sharing status with guaranteed fallback
                            sharing_status = self.get_sharing_status(media)
                            if not sharing_status or not isinstance(sharing_status, dict):
                                sharing_status = {'is_shared': False}
                            
                            media_data = {
                                'id': media.id,
                                'name': media.name,
                                'media_info': media.media_info,
                                'media_type': media.media_type,
                                'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                                'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                                'created_at': media.created_at,
                                'is_test_video': media.is_test_video,
                                'is_about_yourself_video': media.is_about_yourself_video,
                                'sharing_status': sharing_status
                            }
                            item['media_items'].append(media_data)
                return self.get_paginated_response(data)
    
            serializer = self.get_serializer(filtered_queryset.order_by('-id'), many=True)
            data = serializer.data
            for i, item in enumerate(data):
                item['profile_score'] = self.calculate_profile_score(filtered_queryset[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:talent-profile-detail', args=[item['id']]))
                
                # Include media data if requested
                if include_media:
                    item['media_items'] = []
                    for media in filtered_queryset[i].media.all():
                        # Get sharing status with guaranteed fallback
                        sharing_status = self.get_sharing_status(media)
                        if not sharing_status or not isinstance(sharing_status, dict):
                            sharing_status = {'is_shared': False}
                        
                        media_data = {
                            'id': media.id,
                            'name': media.name,
                            'media_info': media.media_info,
                            'media_type': media.media_type,
                            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                            'created_at': media.created_at,
                            'is_test_video': media.is_test_video,
                            'is_about_yourself_video': media.is_about_yourself_video,
                            'sharing_status': sharing_status
                        }
                        item['media_items'].append(media_data)
            return Response(data)

class VisualWorkerSearchView(SearchViewMixin, generics.ListAPIView):
    def get_queryset(self):
        """
        Optimized queryset with annotations to reduce database queries
        """
        return VisualWorker.objects.select_related(
            'profile', 'profile__user'
        ).prefetch_related(
            'profile__media'
        ).annotate(
            # Annotate media counts to avoid N+1 queries
            image_count=Count('profile__media', filter=Q(profile__media__media_type='image', profile__media__is_test_video=False)),
            video_count=Count('profile__media', filter=Q(profile__media__media_type='video', profile__media__is_test_video=False)),
            total_media=Count('profile__media', filter=Q(profile__media__is_test_video=False)),
            # Annotate profile completeness
            profile_complete=F('profile__profile_complete'),
            is_verified=F('profile__is_verified'),
            account_type=F('profile__account_type'),
            city=F('profile__city'),
            country=F('profile__country'),
            # Annotate age calculation
            age=Case(
                When(
                    profile__date_of_birth__isnull=False,
                    then=timezone.now().year - F('profile__date_of_birth__year') - 
                         Case(
                             When(
                                 Q(profile__date_of_birth__month__gt=timezone.now().month) |
                                 Q(profile__date_of_birth__month=timezone.now().month, profile__date_of_birth__day__gt=timezone.now().day),
                                 then=Value(1)
                             ),
                             default=Value(0)
                         )
                ),
                default=Value(None),
                output_field=IntegerField()
            )
        )
    
    serializer_class = VisualWorkerDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = VisualWorkerFilter
    ordering_fields = ['years_experience', 'created_at', 'city', 'country', 'primary_category', 'experience_level']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def calculate_profile_score(self, worker):
        """
        Get the profile score from the associated talent profile's method with caching.
        """
        from .utils import get_profile_score_cached
        profile = worker.profile
        score_breakdown = get_profile_score_cached(profile)
        return score_breakdown['total']
    
    def calculate_relevance_score(self, queryset, filters):
        """
        Calculate a relevance score for each result based on how closely it matches the filter criteria
        Higher score = better match
        """
        query_params = self.request.query_params
        
        # Create a list of profiles with their relevance scores
        workers_with_scores = []
        
        for worker in queryset:
            score = 100  # Start with a perfect score
            
            # Score primary category match
            if 'primary_category' in query_params:
                score += 25 if worker.primary_category == query_params['primary_category'] else 0
            
            # Score experience level match
            if 'experience_level' in query_params:
                score += 20 if worker.experience_level == query_params['experience_level'] else 0
            
            # Score years of experience match
            if 'min_years_experience' in query_params:
                min_exp = int(query_params['min_years_experience'])
                if worker.years_experience >= min_exp:
                    # Exact or higher than requested
                    score += 15
                else:
                    # Penalize for less experience
                    score -= 10 * (min_exp - worker.years_experience)
            
            if 'max_years_experience' in query_params:
                max_exp = int(query_params['max_years_experience'])
                if worker.years_experience <= max_exp:
                    # At or below maximum requested
                    score += 10
                else:
                    # Penalize for being over-experienced
                    score -= 5 * (worker.years_experience - max_exp)
            
            # Score portfolio link - having a portfolio is a plus
            if worker.portfolio_link:
                score += 10
            
            # Score location match
            if 'city' in query_params and worker.city:
                if query_params['city'].lower() in worker.city.lower():
                    score += 15
                elif worker.city.lower() in query_params['city'].lower():
                    score += 10
                    
            if 'country' in query_params and worker.country:
                if query_params['country'].lower() in worker.country.lower():
                    score += 15
                elif worker.country.lower() in query_params['country'].lower():
                    score += 10
            
            # Score availability match
            if 'availability' in query_params:
                score += 15 if worker.availability == query_params['availability'] else 0
            
            # Score rate range match
            if 'rate_range' in query_params:
                score += 15 if worker.rate_range == query_params['rate_range'] else 0
            
            # Score willing to relocate
            if 'willing_to_relocate' in query_params:
                req_relocate = query_params['willing_to_relocate'].lower() in ('true', '1', 'yes')
                score += 10 if worker.willing_to_relocate == req_relocate else 0
            
            # Score profile completeness through the related TalentUserProfile
            if worker.profile.profile_complete:
                score += 5
            
            # Media content bonus
            media_count = worker.profile.media.count()
            if media_count > 10:
                score += 15
            elif media_count > 5:
                score += 10
            elif media_count > 0:
                score += 5
            
            # Verification bonus
            if worker.profile.is_verified:
                score += 10
                
            # Add premium account bonuses - prioritize paid accounts
            if worker.profile.account_type == 'platinum':
                score += 30  # Highest tier gets biggest bonus
            elif worker.profile.account_type == 'gold':
                score += 20  # Medium tier gets medium bonus
            elif worker.profile.account_type == 'silver':
                score += 10  # Basic paid tier gets small bonus
            # Free accounts get no bonus
            
            workers_with_scores.append((worker, score))
        
        # Sort by score descending
        workers_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return workers_with_scores
    
    def list(self, request, *args, **kwargs):
        # Check if media should be included
        include_media = request.query_params.get('include_media', '').lower() == 'true'
        
        # First, apply filtering with the filter_queryset method
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply additional strict filtering for all parameters
        query_params = self.request.query_params
        
        # Apply strict filtering to all parameters
        if 'primary_category' in query_params and query_params['primary_category']:
            queryset = queryset.filter(primary_category=query_params['primary_category'])
        
        if 'experience_level' in query_params and query_params['experience_level']:
            queryset = queryset.filter(experience_level=query_params['experience_level'])
        
        if 'min_years_experience' in query_params:
            try:
                min_exp = int(query_params['min_years_experience'])
                queryset = queryset.filter(years_experience__gte=min_exp)
            except (ValueError, TypeError):
                pass
        
        if 'max_years_experience' in query_params:
            try:
                max_exp = int(query_params['max_years_experience'])
                queryset = queryset.filter(years_experience__lte=max_exp)
            except (ValueError, TypeError):
                pass
        
        # Location filters
        if 'city' in query_params and query_params['city']:
            queryset = queryset.filter(city__icontains=query_params['city'])
        
        if 'country' in query_params and query_params['country']:
            queryset = queryset.filter(country__icontains=query_params['country'])
        
        if 'availability' in query_params and query_params['availability']:
            queryset = queryset.filter(availability=query_params['availability'])
        
        if 'rate_range' in query_params and query_params['rate_range']:
            queryset = queryset.filter(rate_range=query_params['rate_range'])
        
        if 'willing_to_relocate' in query_params:
            willing_to_relocate = query_params['willing_to_relocate'].lower() in ('true', '1', 'yes')
            queryset = queryset.filter(willing_to_relocate=willing_to_relocate)
        
        # If filter parameters are applied, calculate relevance score for the filtered results
        if request.query_params and len(request.query_params) > 0 and queryset.exists():
            workers_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            
            # Extract just the workers from the scored results
            queryset = [worker for worker, score in workers_with_scores]
            
            # Paginate
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                # Add relevance scores, profile scores, and profile URLs to the results
                for i, item in enumerate(data):
                    item['relevance_score'] = workers_with_scores[i][1]
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:visual-worker-detail', args=[item['id']]))
                    
                    # Include media data if requested
                    if include_media:
                        item['media_items'] = []
                        for media in page[i].profile.media.all():
                            # Get sharing status with guaranteed fallback
                            sharing_status = self.get_sharing_status(media)
                            if not sharing_status or not isinstance(sharing_status, dict):
                                sharing_status = {'is_shared': False}
                            
                            media_data = {
                                'id': media.id,
                                'name': media.name,
                                'media_info': media.media_info,
                                'media_type': media.media_type,
                                'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                                'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                                'created_at': media.created_at,
                                'is_test_video': media.is_test_video,
                                'is_about_yourself_video': media.is_about_yourself_video,
                                'sharing_status': sharing_status
                            }
                            item['media_items'].append(media_data)
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            # Add relevance scores, profile scores, and profile URLs to the results
            for i, item in enumerate(data):
                item['relevance_score'] = workers_with_scores[i][1]
                item['profile_score'] = self.calculate_profile_score(page[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:visual-worker-detail', args=[item['id']]))
                
                # Include media data if requested
                if include_media:
                    item['media_items'] = []
                    for media in queryset[i].profile.media.all():
                        # Get sharing status with guaranteed fallback
                        sharing_status = self.get_sharing_status(media)
                        if not sharing_status or not isinstance(sharing_status, dict):
                            sharing_status = {'is_shared': False}
                        
                        media_data = {
                            'id': media.id,
                            'name': media.name,
                            'media_info': media.media_info,
                            'media_type': media.media_type,
                            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                            'created_at': media.created_at,
                            'is_test_video': media.is_test_video,
                            'is_about_yourself_video': media.is_about_yourself_video,
                            'sharing_status': sharing_status
                        }
                        item['media_items'].append(media_data)
            
            return Response(data)
        else:
            # No filters applied or no results after filtering
            if not queryset.exists():
                return Response({"message": "No visual workers match your search criteria."}, status=200)
            
            # Return results sorted by a default field
            page = self.paginate_queryset(queryset.order_by('-id'))
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                for i, item in enumerate(data):
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:visual-worker-detail', args=[item['id']]))
                    
                    # Include media data if requested
                    if include_media:
                        item['media_items'] = []
                        for media in page[i].profile.media.all():
                            # Get sharing status with guaranteed fallback
                            sharing_status = self.get_sharing_status(media)
                            if not sharing_status or not isinstance(sharing_status, dict):
                                sharing_status = {'is_shared': False}
                            
                            media_data = {
                                'id': media.id,
                                'name': media.name,
                                'media_info': media.media_info,
                                'media_type': media.media_type,
                                'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                                'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                                'created_at': media.created_at,
                                'is_test_video': media.is_test_video,
                                'is_about_yourself_video': media.is_about_yourself_video,
                                'sharing_status': sharing_status
                            }
                            item['media_items'].append(media_data)
                
                return self.get_paginated_response(data)
    
            serializer = self.get_serializer(queryset.order_by('-id'), many=True)
            data = serializer.data
            for i, item in enumerate(data):
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:visual-worker-detail', args=[item['id']]))
                
                # Include media data if requested
                if include_media:
                    item['media_items'] = []
                    for media in queryset[i].profile.media.all():
                        # Get sharing status with guaranteed fallback
                        sharing_status = self.get_sharing_status(media)
                        if not sharing_status or not isinstance(sharing_status, dict):
                            sharing_status = {'is_shared': False}
                        
                        media_data = {
                            'id': media.id,
                            'name': media.name,
                            'media_info': media.media_info,
                            'media_type': media.media_type,
                            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                            'created_at': media.created_at,
                            'is_test_video': media.is_test_video,
                            'is_about_yourself_video': media.is_about_yourself_video,
                            'sharing_status': sharing_status
                        }
                        item['media_items'].append(media_data)
            
            return Response(data)

class ExpressiveWorkerSearchView(SearchViewMixin, generics.ListAPIView):
    def get_queryset(self):
        """
        Optimized queryset with annotations to reduce database queries
        """
        return ExpressiveWorker.objects.select_related(
            'profile', 'profile__user'
        ).prefetch_related(
            'profile__media'
        ).annotate(
            # Annotate media counts to avoid N+1 queries
            image_count=Count('profile__media', filter=Q(profile__media__media_type='image', profile__media__is_test_video=False)),
            video_count=Count('profile__media', filter=Q(profile__media__media_type='video', profile__media__is_test_video=False)),
            total_media=Count('profile__media', filter=Q(profile__media__is_test_video=False)),
            # Annotate profile completeness
            profile_complete=F('profile__profile_complete'),
            is_verified=F('profile__is_verified'),
            account_type=F('profile__account_type'),
            city=F('profile__city'),
            country=F('profile__country'),
            # Annotate age calculation
            age=Case(
                When(
                    profile__date_of_birth__isnull=False,
                    then=timezone.now().year - F('profile__date_of_birth__year') - 
                         Case(
                             When(
                                 Q(profile__date_of_birth__month__gt=timezone.now().month) |
                                 Q(profile__date_of_birth__month=timezone.now().month, profile__date_of_birth__day__gt=timezone.now().day),
                                 then=Value(1)
                             ),
                             default=Value(0)
                         )
                ),
                default=Value(None),
                output_field=IntegerField()
            )
        )
    
    serializer_class = ExpressiveWorkerDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ExpressiveWorkerFilter
    ordering_fields = [
        'id', 'performer_type', 'years_experience', 'height', 'weight',
        'hair_color', 'hair_type', 'skin_tone', 'eye_color', 'eye_size', 'eye_pattern',
        'face_shape', 'forehead_shape', 'lip_shape', 'eyebrow_pattern',
        'beard_color', 'beard_length', 'mustache_color', 'mustache_length',
        'distinctive_facial_marks', 'distinctive_body_marks', 'voice_type',
        'body_type', 'availability', 'city', 'country',
        'created_at', 'updated_at'
    ]
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def calculate_profile_score(self, worker):
        """
        Get the profile score from the associated talent profile's method with caching.
        """
        from .utils import get_profile_score_cached
        profile = worker.profile
        score_breakdown = get_profile_score_cached(profile)
        return score_breakdown['total']
    
    def calculate_relevance_score(self, queryset, filters):
        """
        Calculate a relevance score for each result based on how closely it matches the filter criteria
        Higher score = better match
        """
        query_params = self.request.query_params
        
        # Create a list of profiles with their relevance scores
        workers_with_scores = []
        
        for worker in queryset:
            score = 100  # Start with a perfect score
            
            # Score performer type match
            if 'performer_type' in query_params:
                score += 25 if worker.performer_type == query_params['performer_type'] else 0
            
            # Score years of experience match
            if 'min_years_experience' in query_params:
                min_exp = int(query_params['min_years_experience'])
                if worker.years_experience >= min_exp:
                    # Exact or higher than requested
                    score += 15
                else:
                    # Penalize for less experience
                    score -= 10 * (min_exp - worker.years_experience)
            
            if 'max_years_experience' in query_params:
                max_exp = int(query_params['max_years_experience'])
                if worker.years_experience <= max_exp:
                    # At or below maximum requested
                    score += 10
                else:
                    # Penalize for being over-experienced
                    score -= 5 * (worker.years_experience - max_exp)
            
            # Score physical attributes
            if 'hair_color' in query_params:
                score += 10 if worker.hair_color == query_params['hair_color'] else 0
                
            if 'eye_color' in query_params:
                score += 10 if worker.eye_color == query_params['eye_color'] else 0
                
            if 'body_type' in query_params:
                score += 10 if worker.body_type == query_params['body_type'] else 0
            
            # Score location match
            if 'city' in query_params and worker.city:
                if query_params['city'].lower() in worker.city.lower():
                    score += 15
                elif worker.city.lower() in query_params['city'].lower():
                    score += 10
                    
            if 'country' in query_params and worker.country:
                if query_params['country'].lower() in worker.country.lower():
                    score += 15
                elif worker.country.lower() in query_params['country'].lower():
                    score += 10
            
            # Score availability match
            if 'availability' in query_params:
                score += 15 if worker.availability == query_params['availability'] else 0
            
            # Height and weight scoring - closer to target = better score
            if 'height' in query_params:
                target_height = float(query_params['height'])
                height_diff = abs(worker.height - target_height)
                if height_diff < 1:
                    score += 15
                elif height_diff < 3:
                    score += 10
                elif height_diff < 5:
                    score += 5
            
            if 'weight' in query_params:
                target_weight = float(query_params['weight'])
                weight_diff = abs(worker.weight - target_weight)
                if weight_diff < 2:
                    score += 15
                elif weight_diff < 5:
                    score += 10
                elif weight_diff < 10:
                    score += 5
            
            # Score profile completeness through the related TalentUserProfile
            if worker.profile.profile_complete:
                score += 5
            
            # Media content bonus
            media_count = worker.profile.media.count()
            if media_count > 10:
                score += 15
            elif media_count > 5:
                score += 10
            elif media_count > 0:
                score += 5
            
            # Verification bonus
            if worker.profile.is_verified:
                score += 10
                
            # Add premium account bonuses - prioritize paid accounts
            if worker.profile.account_type == 'platinum':
                score += 30  # Highest tier gets biggest bonus
            elif worker.profile.account_type == 'gold':
                score += 20  # Medium tier gets medium bonus
            elif worker.profile.account_type == 'silver':
                score += 10  # Basic paid tier gets small bonus
            # Free accounts get no bonus
            
            workers_with_scores.append((worker, score))
        
        # Sort by score descending
        workers_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return workers_with_scores
    
    def list(self, request, *args, **kwargs):
        # Always include media items with sharing status
        include_media = True
        
        # First, apply filtering with the filter_queryset method
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply additional strict filtering for all parameters
        query_params = self.request.query_params
        
        # Apply strict filtering to all parameters
        if 'performer_type' in query_params and query_params['performer_type']:
            queryset = queryset.filter(performer_type=query_params['performer_type'])
        
        if 'min_years_experience' in query_params:
            try:
                min_exp = int(query_params['min_years_experience'])
                queryset = queryset.filter(years_experience__gte=min_exp)
            except (ValueError, TypeError):
                pass
        
        if 'max_years_experience' in query_params:
            try:
                max_exp = int(query_params['max_years_experience'])
                queryset = queryset.filter(years_experience__lte=max_exp)
            except (ValueError, TypeError):
                pass
        
        # Physical attributes - strict matching
        if 'hair_color' in query_params and query_params['hair_color']:
            queryset = queryset.filter(hair_color=query_params['hair_color'])
        
        if 'eye_color' in query_params and query_params['eye_color']:
            queryset = queryset.filter(eye_color=query_params['eye_color'])
        
        if 'body_type' in query_params and query_params['body_type']:
            queryset = queryset.filter(body_type=query_params['body_type'])
        
        # Height with tolerance
        if 'height' in query_params:
            try:
                target_height = float(query_params['height'])
                # Apply a small tolerance of +/- 2cm
                tolerance = float(query_params.get('height_tolerance', 2))
                queryset = queryset.filter(
                    height__gte=target_height-tolerance,
                    height__lte=target_height+tolerance
                )
            except (ValueError, TypeError):
                pass
        
        # Weight with tolerance
        if 'weight' in query_params:
            try:
                target_weight = float(query_params['weight'])
                # Apply a small tolerance of +/- 2kg
                tolerance = float(query_params.get('weight_tolerance', 2))
                queryset = queryset.filter(
                    weight__gte=target_weight-tolerance,
                    weight__lte=target_weight+tolerance
                )
            except (ValueError, TypeError):
                pass
        
        # Location filters
        if 'city' in query_params and query_params['city']:
            queryset = queryset.filter(city__icontains=query_params['city'])
        
        if 'country' in query_params and query_params['country']:
            queryset = queryset.filter(country__icontains=query_params['country'])
        
        if 'availability' in query_params and query_params['availability']:
            queryset = queryset.filter(availability=query_params['availability'])
        
        # If filter parameters are applied, calculate relevance score for the filtered results
        if request.query_params and len(request.query_params) > 0 and queryset.exists():
            workers_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            
            # Extract just the workers from the scored results
            queryset = [worker for worker, score in workers_with_scores]
            
            # Paginate
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                # Add relevance scores, profile scores, and profile URLs to the results
                for i, item in enumerate(data):
                    item['relevance_score'] = workers_with_scores[i][1]
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:expressive-worker-detail', args=[item['id']]))
                
                    # Always include media data with sharing status
                    item['media_items'] = []
                    for media in page[i].profile.media.all():
                        sharing_status = self.get_sharing_status(media)
                        if not sharing_status or not isinstance(sharing_status, dict):
                            sharing_status = {'is_shared': False}
                        media_data = {
                            'id': media.id,
                            'name': media.name,
                            'media_info': media.media_info,
                            'media_type': media.media_type,
                            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                            'created_at': media.created_at,
                            'is_test_video': media.is_test_video,
                            'is_about_yourself_video': media.is_about_yourself_video,
                            'sharing_status': sharing_status
                        }
                        item['media_items'].append(media_data)
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            for i, item in enumerate(data):
                item['relevance_score'] = workers_with_scores[i][1]
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:expressive-worker-detail', args=[item['id']]))
                # Always include media data with sharing status
                item['media_items'] = []
                for media in queryset[i].profile.media.all():
                    sharing_status = self.get_sharing_status(media)
                    if not sharing_status or not isinstance(sharing_status, dict):
                        sharing_status = {'is_shared': False}
                    media_data = {
                        'id': media.id,
                        'name': media.name,
                        'media_info': media.media_info,
                        'media_type': media.media_type,
                        'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                        'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                        'created_at': media.created_at,
                        'is_test_video': media.is_test_video,
                        'is_about_yourself_video': media.is_about_yourself_video,
                        'sharing_status': sharing_status
                    }
                    item['media_items'].append(media_data)
            return Response(data)
        else:
            if not queryset.exists():
                return Response({"message": "No expressive workers match your search criteria."}, status=200)
            page = self.paginate_queryset(queryset.order_by('-id'))
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                for i, item in enumerate(data):
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:expressive-worker-detail', args=[item['id']]))
                    # Always include media data with sharing status
                    item['media_items'] = []
                    for media in page[i].profile.media.all():
                        sharing_status = self.get_sharing_status(media)
                        if not sharing_status or not isinstance(sharing_status, dict):
                            sharing_status = {'is_shared': False}
                        media_data = {
                            'id': media.id,
                            'name': media.name,
                            'media_info': media.media_info,
                            'media_type': media.media_type,
                            'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                            'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                            'created_at': media.created_at,
                            'is_test_video': media.is_test_video,
                            'is_about_yourself_video': media.is_about_yourself_video,
                            'sharing_status': sharing_status
                        }
                        item['media_items'].append(media_data)
                return self.get_paginated_response(data)
            serializer = self.get_serializer(queryset.order_by('-id'), many=True)
            data = serializer.data
            for i, item in enumerate(data):
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:expressive-worker-detail', args=[item['id']]))
                # Always include media data with sharing status
                item['media_items'] = []
                for media in queryset[i].profile.media.all():
                    sharing_status = self.get_sharing_status(media)
                    if not sharing_status or not isinstance(sharing_status, dict):
                        sharing_status = {'is_shared': False}
                    media_data = {
                        'id': media.id,
                        'name': media.name,
                        'media_info': media.media_info,
                        'media_type': media.media_type,
                        'media_file': request.build_absolute_uri(media.media_file.url) if media.media_file else None,
                        'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None,
                        'created_at': media.created_at,
                        'is_test_video': media.is_test_video,
                        'is_about_yourself_video': media.is_about_yourself_video,
                        'sharing_status': sharing_status
                    }
                    item['media_items'].append(media_data)
            return Response(data)

class HybridWorkerSearchView(SearchViewMixin, generics.ListAPIView):
    def get_queryset(self):
        """
        Optimized queryset with annotations to reduce database queries
        """
        return HybridWorker.objects.select_related(
            'profile', 'profile__user'
        ).prefetch_related(
            'profile__media'
        ).annotate(
            # Annotate media counts to avoid N+1 queries
            image_count=Count('profile__media', filter=Q(profile__media__media_type='image', profile__media__is_test_video=False)),
            video_count=Count('profile__media', filter=Q(profile__media__media_type='video', profile__media__is_test_video=False)),
            total_media=Count('profile__media', filter=Q(profile__media__is_test_video=False)),
            # Annotate profile completeness
            profile_complete=F('profile__profile_complete'),
            is_verified=F('profile__is_verified'),
            account_type=F('profile__account_type'),
            city=F('profile__city'),
            country=F('profile__country'),
            # Annotate age calculation
            age=Case(
                When(
                    profile__date_of_birth__isnull=False,
                    then=timezone.now().year - F('profile__date_of_birth__year') - 
                         Case(
                             When(
                                 Q(profile__date_of_birth__month__gt=timezone.now().month) |
                                 Q(profile__date_of_birth__month=timezone.now().month, profile__date_of_birth__day__gt=timezone.now().day),
                                 then=Value(1)
                             ),
                             default=Value(0)
                         )
                ),
                default=Value(None),
                output_field=IntegerField()
            )
        )
    
    serializer_class = HybridWorkerDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = HybridWorkerFilter
    ordering_fields = ['years_experience', 'created_at', 'city', 'country', 'hybrid_type', 'hair_color', 'eye_color', 'skin_tone', 'body_type', 'fitness_level', 'risk_levels']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def calculate_profile_score(self, worker):
        """
        Get the profile score from the associated talent profile's method with caching.
        """
        from .utils import get_profile_score_cached
        profile = worker.profile
        score_breakdown = get_profile_score_cached(profile)
        return score_breakdown['total']
    
    def calculate_relevance_score(self, queryset, filters):
        """
        Calculate a relevance score for each result based on how closely it matches the filter criteria
        Higher score = better match
        """
        query_params = self.request.query_params
        
        # Create a list of profiles with their relevance scores
        workers_with_scores = []
        
        for worker in queryset:
            score = 100  # Start with a perfect score
            
            # Score hybrid type match
            if 'hybrid_type' in query_params:
                score += 25 if worker.hybrid_type == query_params['hybrid_type'] else 0
            
            # Score years of experience match
            if 'min_years_experience' in query_params:
                min_exp = int(query_params['min_years_experience'])
                if worker.years_experience >= min_exp:
                    # Exact or higher than requested
                    score += 15
                else:
                    # Penalize for less experience
                    score -= 10 * (min_exp - worker.years_experience)
            
            if 'max_years_experience' in query_params:
                max_exp = int(query_params['max_years_experience'])
                if worker.years_experience <= max_exp:
                    # At or below maximum requested
                    score += 10
                else:
                    # Penalize for being over-experienced
                    score -= 5 * (worker.years_experience - max_exp)
            
            # Score physical attributes
            if 'hair_color' in query_params:
                score += 10 if worker.hair_color == query_params['hair_color'] else 0
                
            if 'eye_color' in query_params:
                score += 10 if worker.eye_color == query_params['eye_color'] else 0
                
            if 'skin_tone' in query_params:
                score += 10 if worker.skin_tone == query_params['skin_tone'] else 0
                
            if 'body_type' in query_params:
                score += 10 if worker.body_type == query_params['body_type'] else 0
                
            if 'fitness_level' in query_params:
                score += 15 if worker.fitness_level == query_params['fitness_level'] else 0
                
            if 'risk_levels' in query_params:
                score += 15 if worker.risk_levels == query_params['risk_levels'] else 0
            
            # Score location match
            if 'city' in query_params and worker.city:
                if query_params['city'].lower() in worker.city.lower():
                    score += 15
                elif worker.city.lower() in query_params['city'].lower():
                    score += 10
                    
            if 'country' in query_params and worker.country:
                if query_params['country'].lower() in worker.country.lower():
                    score += 15
                elif worker.country.lower() in query_params['country'].lower():
                    score += 10
            
            # Score availability match
            if 'availability' in query_params:
                score += 15 if worker.availability == query_params['availability'] else 0
            
            # Score willing to relocate
            if 'willing_to_relocate' in query_params:
                req_relocate = query_params['willing_to_relocate'].lower() in ('true', '1', 'yes')
                score += 10 if worker.willing_to_relocate == req_relocate else 0
            
            # Height and weight scoring - closer to target = better score
            if 'height' in query_params:
                target_height = float(query_params['height'])
                height_diff = abs(worker.height - target_height)
                if height_diff < 1:
                    score += 15
                elif height_diff < 3:
                    score += 10
                elif height_diff < 5:
                    score += 5
            
            if 'weight' in query_params:
                target_weight = float(query_params['weight'])
                weight_diff = abs(worker.weight - target_weight)
                if weight_diff < 2:
                    score += 15
                elif weight_diff < 5:
                    score += 10
                elif weight_diff < 10:
                    score += 5
            
            # Score profile completeness through the related TalentUserProfile
            if worker.profile.profile_complete:
                score += 5
            
            # Media content bonus
            media_count = worker.profile.media.count()
            if media_count > 10:
                score += 15
            elif media_count > 5:
                score += 10
            elif media_count > 0:
                score += 5
            
            # Verification bonus
            if worker.profile.is_verified:
                score += 10
                
            # Add premium account bonuses - prioritize paid accounts
            if worker.profile.account_type == 'platinum':
                score += 30  # Highest tier gets biggest bonus
            elif worker.profile.account_type == 'gold':
                score += 20  # Medium tier gets medium bonus
            elif worker.profile.account_type == 'silver':
                score += 10  # Basic paid tier gets small bonus
            # Free accounts get no bonus
            
            workers_with_scores.append((worker, score))
        
        # Sort by score descending
        workers_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return workers_with_scores
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # If filter parameters are applied, calculate relevance score
        if request.query_params and len(request.query_params) > 0:
            workers_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            
            # Extract just the workers from the scored results
            queryset = [worker for worker, score in workers_with_scores]
            
            # Paginate
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                # Add relevance scores and profile URLs to the results
                for i, item in enumerate(data):
                    item['relevance_score'] = workers_with_scores[i][1]
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:hybrid-worker-detail', args=[item['id']]))
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            # Add relevance scores and profile URLs to the results
            for i, item in enumerate(data):
                item['relevance_score'] = workers_with_scores[i][1]
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:hybrid-worker-detail', args=[item['id']]))
            
            return Response(data)
        else:
            # No filters applied, just return all results
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                for i, item in enumerate(data):
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:hybrid-worker-detail', args=[item['id']]))
                return self.get_paginated_response(data)
    
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            for i, item in enumerate(data):
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:hybrid-worker-detail', args=[item['id']]))
            return Response(data)

class BackGroundJobsProfileSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = BackGroundJobsProfile.objects.all().select_related('user')
    serializer_class = BackGroundDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = BackGroundJobsProfileFilter
    ordering_fields = ['date_of_birth', 'country', 'account_type']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]

    def calculate_profile_score(self, profile):
        """
        Get the profile score from the model's method.
        """
        score_breakdown = profile.get_profile_score()
        return score_breakdown['total']
    
    def calculate_relevance_score(self, queryset, filters):
        """Calculate relevance score for background profiles"""
        query_params = self.request.query_params
        profiles_with_scores = []
        
        for profile in queryset:
            score = 100
            
            if 'gender' in query_params:
                score += 20 if profile.gender == query_params['gender'] else 0
            
            if 'country' in query_params and profile.country:
                if query_params['country'].lower() in profile.country.lower():
                    score += 15
            
            if 'account_type' in query_params:
                score += 15 if profile.account_type == query_params['account_type'] else 0
            
            profiles_with_scores.append((profile, score))
        
        profiles_with_scores.sort(key=lambda x: x[1], reverse=True)
        return profiles_with_scores
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if request.query_params and len(request.query_params) > 0:
            profiles_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            queryset = [profile for profile, score in profiles_with_scores]
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                for i, item in enumerate(data):
                    item['relevance_score'] = profiles_with_scores[i][1]
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:background-profile-detail', args=[item['id']]))
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            for i, item in enumerate(data):
                item['relevance_score'] = profiles_with_scores[i][1]
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:background-profile-detail', args=[item['id']]))
            
            return Response(data)
        else:
            page = self.paginate_queryset(queryset.order_by('-id'))
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                for i, item in enumerate(data):
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['profile_url'] = request.build_absolute_uri(reverse('dashboard:background-profile-detail', args=[item['id']]))
                return self.get_paginated_response(data)
    
            serializer = self.get_serializer(queryset.order_by('-id'), many=True)
            data = serializer.data
            for i, item in enumerate(data):
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['profile_url'] = request.build_absolute_uri(reverse('dashboard:background-profile-detail', args=[item['id']]))
            return Response(data)

class PropSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = Prop.objects.select_related('BackGroundJobsProfile__user')
    serializer_class = PropDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PropFilter
    ordering_fields = ['name', 'price', 'created_at']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def calculate_relevance_score(self, queryset, filters):
        query_params = self.request.query_params
        items_with_scores = []
        
        # Simple field mappings for props
        field_mappings = {
            'name': ('name', 20),
            'material': ('material', 15),
            'condition': ('condition', 10)
        }
        
        for item in queryset:
            relevance_score = self.calculate_simple_relevance_score(item, query_params, field_mappings)
            items_with_scores.append((item, relevance_score))
        
        items_with_scores.sort(key=lambda x: x[1], reverse=True)
        return items_with_scores
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if request.query_params and len(request.query_params) > 0:
            items_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            queryset = [item for item, score in items_with_scores]
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                for i, item in enumerate(data):
                    item['relevance_score'] = items_with_scores[i][1]
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            for i, item in enumerate(data):
                item['relevance_score'] = items_with_scores[i][1]
            
            return Response(data)
        else:
            return super().list(request, *args, **kwargs)

class CostumeSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = Costume.objects.select_related('BackGroundJobsProfile__user')
    serializer_class = CostumeDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = CostumeFilter
    ordering_fields = ['name', 'price', 'created_at', 'size', 'era']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def calculate_relevance_score(self, queryset, filters):
        query_params = self.request.query_params
        items_with_scores = []
        
        for item in queryset:
            score = 100
            
            if 'name' in query_params and item.name:
                if query_params['name'].lower() in item.name.lower():
                    score += 20
            
            if 'size' in query_params and item.size:
                if item.size == query_params['size']:
                    score += 15
            
            if 'era' in query_params and item.era:
                if query_params['era'].lower() in item.era.lower():
                    score += 15
            
            items_with_scores.append((item, score))
        
        items_with_scores.sort(key=lambda x: x[1], reverse=True)
        return items_with_scores
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if request.query_params and len(request.query_params) > 0:
            items_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            queryset = [item for item, score in items_with_scores]
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                for i, item in enumerate(data):
                    item['relevance_score'] = items_with_scores[i][1]
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            for i, item in enumerate(data):
                item['relevance_score'] = items_with_scores[i][1]
            
            return Response(data)
        else:
            return super().list(request, *args, **kwargs)

class LocationSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = Location.objects.select_related('BackGroundJobsProfile__user')
    serializer_class = LocationDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = LocationFilter
    ordering_fields = ['name', 'price', 'created_at', 'location_type']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def calculate_relevance_score(self, queryset, filters):
        query_params = self.request.query_params
        items_with_scores = []
        
        for item in queryset:
            score = 100
            
            if 'name' in query_params and item.name:
                if query_params['name'].lower() in item.name.lower():
                    score += 20
            
            if 'address' in query_params and item.address:
                if query_params['address'].lower() in item.address.lower():
                    score += 15
            
            if 'is_indoor' in query_params:
                is_indoor = query_params['is_indoor'].lower() in ('true', '1', 'yes')
                if item.is_indoor == is_indoor:
                    score += 10
            
            items_with_scores.append((item, score))
        
        items_with_scores.sort(key=lambda x: x[1], reverse=True)
        return items_with_scores
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if request.query_params and len(request.query_params) > 0:
            items_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            queryset = [item for item, score in items_with_scores]
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                for i, item in enumerate(data):
                    item['relevance_score'] = items_with_scores[i][1]
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            for i, item in enumerate(data):
                item['relevance_score'] = items_with_scores[i][1]
            
            return Response(data)
        else:
            return super().list(request, *args, **kwargs)

class MemorabiliaSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = Memorabilia.objects.select_related('BackGroundJobsProfile__user')
    serializer_class = MemorabilaDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = MemorabiliaFilter
    ordering_fields = ['name', 'price', 'created_at', 'signed_by']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def calculate_relevance_score(self, queryset, filters):
        query_params = self.request.query_params
        items_with_scores = []
        
        for item in queryset:
            score = 100
            
            if 'name' in query_params and item.name:
                if query_params['name'].lower() in item.name.lower():
                    score += 20
            
            if 'signed_by' in query_params and item.signed_by:
                if query_params['signed_by'].lower() in item.signed_by.lower():
                    score += 25
            
            items_with_scores.append((item, score))
        
        items_with_scores.sort(key=lambda x: x[1], reverse=True)
        return items_with_scores
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if request.query_params and len(request.query_params) > 0:
            items_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            queryset = [item for item, score in items_with_scores]
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                for i, item in enumerate(data):
                    item['relevance_score'] = items_with_scores[i][1]
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            for i, item in enumerate(data):
                item['relevance_score'] = items_with_scores[i][1]
            
            return Response(data)
        else:
            return super().list(request, *args, **kwargs)

class VehicleSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = Vehicle.objects.select_related('BackGroundJobsProfile__user')
    serializer_class = VehicleDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = VehicleFilter
    ordering_fields = ['name', 'price', 'created_at', 'make', 'model', 'year']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def calculate_relevance_score(self, queryset, filters):
        query_params = self.request.query_params
        items_with_scores = []
        
        for item in queryset:
            score = 100
            
            if 'make' in query_params and item.make:
                if query_params['make'].lower() in item.make.lower():
                    score += 20
            
            if 'model' in query_params and item.model:
                if query_params['model'].lower() in item.model.lower():
                    score += 20
            
            if 'year' in query_params and item.year:
                try:
                    target_year = int(query_params['year'])
                    if item.year == target_year:
                        score += 15
                except (ValueError, TypeError):
                    pass
            
            items_with_scores.append((item, score))
        
        items_with_scores.sort(key=lambda x: x[1], reverse=True)
        return items_with_scores
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if request.query_params and len(request.query_params) > 0:
            items_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            queryset = [item for item, score in items_with_scores]
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                for i, item in enumerate(data):
                    item['relevance_score'] = items_with_scores[i][1]
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            for i, item in enumerate(data):
                item['relevance_score'] = items_with_scores[i][1]
            
            return Response(data)
        else:
            return super().list(request, *args, **kwargs)

class ArtisticMaterialSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = ArtisticMaterial.objects.select_related('BackGroundJobsProfile__user')
    serializer_class = ArtisticMaterialDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ArtisticMaterialFilter
    ordering_fields = ['name', 'price', 'created_at', 'type']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]

class MusicItemSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = MusicItem.objects.select_related('BackGroundJobsProfile__user')
    serializer_class = MusicItemDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = MusicItemFilter
    ordering_fields = ['name', 'price', 'created_at', 'instrument_type']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]

class RareItemSearchView(SearchViewMixin, generics.ListAPIView):
    queryset = RareItem.objects.select_related('BackGroundJobsProfile__user')
    serializer_class = RareItemDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RareItemFilter
    ordering_fields = ['name', 'price', 'created_at', 'provenance']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]

class BandSearchView(SearchViewMixin, generics.ListAPIView):
    def get_queryset(self):
        """
        Optimized queryset with annotations to reduce database queries
        """
        return Band.objects.select_related(
            'creator', 'creator__user'
        ).prefetch_related(
            'members', 'media', 'bandmembership'
        ).annotate(
            # Annotate member count to avoid N+1 queries
            member_count=Count('bandmembership'),
            admin_count=Count('bandmembership', filter=Q(bandmembership__role='admin')),
            # Annotate media count
            media_count=Count('media'),
            # Annotate creator info
            creator_email=F('creator__user__email'),
            creator_name=Case(
                When(
                    creator__user__first_name__isnull=False,
                    creator__user__last_name__isnull=False,
                    then=Concat('creator__user__first_name', Value(' '), 'creator__user__last_name')
                ),
                When(
                    creator__user__first_name__isnull=False,
                    then='creator__user__first_name'
                ),
                When(
                    creator__user__last_name__isnull=False,
                    then='creator__user__last_name'
                ),
                default='creator__user__email',
                output_field=CharField()
            )
        )
    
    serializer_class = BandDashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = BandFilter
    ordering_fields = ['name', 'created_at', 'band_type', 'location']
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def calculate_profile_score(self, band):
        """
        Get the profile score from the band's method with caching.
        """
        from .utils import get_profile_score_cached
        score_breakdown = get_profile_score_cached(band)
        return score_breakdown['total']
    
    def calculate_relevance_score(self, queryset, filters):
        """
        Calculate a relevance score for each result based on how closely it matches the filter criteria
        Higher score = better match
        """
        query_params = self.request.query_params
        
        # Create a list of bands with their relevance scores
        bands_with_scores = []
        
        for band in queryset:
            score = 100  # Start with a perfect score
            
            # Score band type match
            if 'band_type' in query_params:
                score += 25 if band.band_type == query_params['band_type'] else 0
            
            # Score band name match (partial match can still get points)
            if 'name' in query_params and band.name:
                if query_params['name'].lower() in band.name.lower():
                    score += 20
                elif band.name.lower() in query_params['name'].lower():
                    score += 15
            
            # Score location match
            if 'location' in query_params and band.location:
                if query_params['location'].lower() in band.location.lower():
                    score += 15
                elif band.location.lower() in query_params['location'].lower():
                    score += 10
            
            # Score member count match
            if 'min_members' in query_params:
                min_members = int(query_params['min_members'])
                if band.member_count >= min_members:
                    score += 10
                else:
                    # Penalize for having fewer members than requested
                    score -= 5 * (min_members - band.member_count)
            
            if 'max_members' in query_params:
                max_members = int(query_params['max_members'])
                if band.member_count <= max_members:
                    score += 5
                else:
                    # Penalize for having more members than requested
                    score -= 2 * (band.member_count - max_members)
            
            # Score media count - bands with more media might be more appealing
            media_count = band.media.count()
            if media_count > 3:
                score += 15
            elif media_count > 1:
                score += 10
            elif media_count > 0:
                score += 5
            
            bands_with_scores.append((band, score))
        
        # Sort by score descending
        bands_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return the sorted bands and their scores
        return bands_with_scores
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # If filter parameters are applied, calculate relevance score
        if request.query_params and len(request.query_params) > 0:
            bands_with_scores = self.calculate_relevance_score(queryset, request.query_params)
            
            # Extract just the bands from the scored results
            queryset = [band for band, score in bands_with_scores]
            
            # Paginate
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                
                # Add relevance scores and band URLs to the results
                for i, item in enumerate(data):
                    item['relevance_score'] = bands_with_scores[i][1]
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['band_url'] = request.build_absolute_uri(reverse('dashboard:band-detail', args=[item['id']]))
                
                return self.get_paginated_response(data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            # Add relevance scores and band URLs to the results
            for i, item in enumerate(data):
                item['relevance_score'] = bands_with_scores[i][1]
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['band_url'] = request.build_absolute_uri(reverse('dashboard:band-detail', args=[item['id']]))
            
            return Response(data)
        else:
            # No filters applied, just return all results
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                for i, item in enumerate(data):
                    item['profile_score'] = self.calculate_profile_score(page[i])
                    item['band_url'] = request.build_absolute_uri(reverse('dashboard:band-detail', args=[item['id']]))
                return self.get_paginated_response(data)
    
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            for i, item in enumerate(data):
                item['profile_score'] = self.calculate_profile_score(queryset[i])
                item['band_url'] = request.build_absolute_uri(reverse('dashboard:band-detail', args=[item['id']]))
            return Response(data)

class UnifiedSearchView(SearchViewMixin, generics.GenericAPIView):
    """
    Unified search endpoint for all profile types in the platform.
    
    This single endpoint handles searching across all profile types including:
    - Talent profiles (talent, visual, expressive, hybrid)
    - Background accounts and items (background, props, costumes, etc.)
    - Bands
    
    Parameters:
    - profile_type: The type of profile to search for. Options include:
        - talent: TalentUserProfile (default)
        - visual: VisualWorker
        - expressive: ExpressiveWorker
        - hybrid: HybridWorker
        - background: BackGroundJobsProfile
        - props: Prop
        - costumes: Costume
        - locations: Location
        - memorabilia: Memorabilia
        - vehicles: Vehicle
        - artistic_materials: ArtisticMaterial
        - music_items: MusicItem
        - rare_items: RareItem
        - bands: Band
    
    Filter parameters:
    - All filter parameters for the selected profile_type can be used directly
    - Each profile type has its own specific filtering options
    
    Response:
    - Returns a consistent response format with relevance scores
    - Results are sorted by relevance to the search criteria
    
    Examples:
    - /api/dashboard/search/?profile_type=talent&gender=female&city=London
    - /api/dashboard/search/?profile_type=visual&primary_category=photographer
    - /api/dashboard/search/?profile_type=bands&band_type=musical
    - /api/dashboard/search/?profile_type=props&min_price=100&max_price=500
    """
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get(self, request, *args, **kwargs):
        # Get profile type from request
        profile_type = request.query_params.get('profile_type', 'talent').lower()
        
        # Extract search criteria, skipping profile_type and format
        search_criteria = {k: v for k, v in request.query_params.items() 
                          if k != 'format' and (k != 'profile_type' or k == 'profile_type' and profile_type != 'talent')}
        
        # Map profile types to their respective view classes
        profile_views = {
            'talent': TalentUserProfileSearchView,
            'visual': VisualWorkerSearchView,
            'expressive': ExpressiveWorkerSearchView,
            'hybrid': HybridWorkerSearchView,
            'background': BackGroundJobsProfileSearchView,
            'props': PropSearchView,
            'costumes': CostumeSearchView,
            'locations': LocationSearchView,
            'memorabilia': MemorabiliaSearchView,
            'vehicles': VehicleSearchView,
            'artistic_materials': ArtisticMaterialSearchView,
            'music_items': MusicItemSearchView,
            'rare_items': RareItemSearchView,
            'bands': BandSearchView
        }
        
        # Check if the profile type is valid
        if profile_type not in profile_views:
            return Response(
                {'error': f'Invalid profile_type: {profile_type}. Must be one of: {", ".join(profile_views.keys())}'},
                status=400
            )
        
        # Log search criteria
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Search criteria: {search_criteria}")
        
        # Create an instance of the appropriate view
        view_class = profile_views[profile_type]
        view = view_class()
        
        # Properly initialize the view
        view.request = request
        view.format_kwarg = self.format_kwarg
        view.kwargs = kwargs
        view.args = args
        
        # Get response from the view
        try:
            original_response = view.list(request)
        
            # Check if the response contains a message about no results
            if isinstance(original_response.data, dict) and 'message' in original_response.data:
                # Include the profile type in the message for clarity
                return Response({
                    'success': True,
                    'profile_type': profile_type,
                    'message': f"No {profile_type} profiles match your search criteria.",
                    'count': 0,
                    'search_criteria': search_criteria,
                    'results': []
                })
            
            # For paginated responses, restructure the response
            if hasattr(original_response, 'data') and 'results' in original_response.data:
                # Paginated response
                results = original_response.data['results']
                count = original_response.data.get('count', len(results))
                
                # Extract pagination links if they exist
                next_link = original_response.data.get('next', None)
                previous_link = original_response.data.get('previous', None)
                
                # Create enhanced response with metadata
                response_data = {
                    'success': True,
                    'profile_type': profile_type,
                    'count': count,
                    'search_criteria': search_criteria,
                    'results': results
                }
                
                # Add pagination links if present
                if next_link:
                    response_data['next'] = next_link
                if previous_link:
                    response_data['previous'] = previous_link
                    
                return Response(response_data)
            else:
                # Non-paginated response
                results = original_response.data
                count = len(results)
                
                # Create enhanced response with metadata
                return Response({
                    'success': True,
                    'profile_type': profile_type,
                    'count': count,
                    'search_criteria': search_criteria,
                    'results': results
                })
            
        except Exception as e:
            # Log the error and provide a helpful message
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in UnifiedSearchView: {str(e)}")
            return Response({
                'success': False,
                'profile_type': profile_type,
                'error': f'An error occurred while searching for {profile_type} profiles: {str(e)}'
            }, status=500)

