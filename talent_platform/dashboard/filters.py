import django_filters
import datetime
from profiles.models import (
    TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker, BackGroundJobsProfile,
    Prop, Costume, Location, Memorabilia, Vehicle, ArtisticMaterial, MusicItem, RareItem,
    Band
)

class TalentUserProfileFilter(django_filters.FilterSet):
    gender = django_filters.CharFilter(lookup_expr='iexact')
    city = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='icontains')
    account_type = django_filters.CharFilter(lookup_expr='iexact')
    is_verified = django_filters.BooleanFilter()
    age = django_filters.NumberFilter(method='filter_by_age')

    def filter_by_age(self, queryset, name, value):
        today = datetime.date.today()
        dob_start = today.replace(year=today.year - value - 1) + datetime.timedelta(days=1)
        dob_end = today.replace(year=today.year - value)
        return queryset.filter(date_of_birth__gte=dob_start, date_of_birth__lte=dob_end)

    class Meta:
        model = TalentUserProfile
        fields = ['gender', 'city', 'country', 'account_type', 'is_verified', 'age']

class VisualWorkerFilter(django_filters.FilterSet):
    primary_category = django_filters.CharFilter(lookup_expr='iexact')
    experience_level = django_filters.CharFilter(lookup_expr='iexact')
    min_years_experience = django_filters.NumberFilter(field_name='years_experience', lookup_expr='gte')
    max_years_experience = django_filters.NumberFilter(field_name='years_experience', lookup_expr='lte')
    city = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='icontains')
    profile_gender = django_filters.CharFilter(field_name='profile__gender', lookup_expr='iexact')
    profile_age = django_filters.NumberFilter(method='filter_by_profile_age')

    def filter_by_profile_age(self, queryset, name, value):
        today = datetime.date.today()
        dob_start = today.replace(year=today.year - value - 1) + datetime.timedelta(days=1)
        dob_end = today.replace(year=today.year - value)
        return queryset.filter(profile__date_of_birth__gte=dob_start, profile__date_of_birth__lte=dob_end)

    class Meta:
        model = VisualWorker
        fields = ['primary_category', 'experience_level', 'city', 'country', 'profile_gender', 'profile_age', 'min_years_experience', 'max_years_experience']

class ExpressiveWorkerFilter(django_filters.FilterSet):
    performer_type = django_filters.CharFilter(lookup_expr='iexact')
    min_years_experience = django_filters.NumberFilter(field_name='years_experience', lookup_expr='gte')
    max_years_experience = django_filters.NumberFilter(field_name='years_experience', lookup_expr='lte')
    hair_color = django_filters.CharFilter(lookup_expr='iexact')
    eye_color = django_filters.CharFilter(lookup_expr='iexact')
    body_type = django_filters.CharFilter(lookup_expr='iexact')
    city = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='icontains')
    profile_gender = django_filters.CharFilter(field_name='profile__gender', lookup_expr='iexact')
    profile_age = django_filters.NumberFilter(method='filter_by_profile_age')

    def filter_by_profile_age(self, queryset, name, value):
        today = datetime.date.today()
        dob_start = today.replace(year=today.year - value - 1) + datetime.timedelta(days=1)
        dob_end = today.replace(year=today.year - value)
        return queryset.filter(profile__date_of_birth__gte=dob_start, profile__date_of_birth__lte=dob_end)

    class Meta:
        model = ExpressiveWorker
        fields = ['performer_type', 'hair_color', 'eye_color', 'body_type', 'city', 'country', 'profile_gender', 'profile_age', 'min_years_experience', 'max_years_experience']

class HybridWorkerFilter(django_filters.FilterSet):
    hybrid_type = django_filters.CharFilter(lookup_expr='iexact')
    min_years_experience = django_filters.NumberFilter(field_name='years_experience', lookup_expr='gte')
    max_years_experience = django_filters.NumberFilter(field_name='years_experience', lookup_expr='lte')
    hair_color = django_filters.CharFilter(lookup_expr='iexact')
    eye_color = django_filters.CharFilter(lookup_expr='iexact')
    skin_tone = django_filters.CharFilter(lookup_expr='iexact')
    body_type = django_filters.CharFilter(lookup_expr='iexact')
    fitness_level = django_filters.CharFilter(lookup_expr='iexact')
    risk_levels = django_filters.CharFilter(lookup_expr='iexact')
    city = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='icontains')
    profile_gender = django_filters.CharFilter(field_name='profile__gender', lookup_expr='iexact')
    profile_age = django_filters.NumberFilter(method='filter_by_profile_age')

    def filter_by_profile_age(self, queryset, name, value):
        today = datetime.date.today()
        dob_start = today.replace(year=today.year - value - 1) + datetime.timedelta(days=1)
        dob_end = today.replace(year=today.year - value)
        return queryset.filter(profile__date_of_birth__gte=dob_start, profile__date_of_birth__lte=dob_end)

    class Meta:
        model = HybridWorker
        fields = ['hybrid_type', 'hair_color', 'eye_color', 'skin_tone', 'body_type', 'fitness_level', 'risk_levels', 'city', 'country', 'profile_gender', 'profile_age', 'min_years_experience', 'max_years_experience']

class BackGroundJobsProfileFilter(django_filters.FilterSet):
    gender = django_filters.CharFilter(lookup_expr='iexact')
    country = django_filters.CharFilter(lookup_expr='icontains')
    account_type = django_filters.CharFilter(lookup_expr='iexact')
    min_age = django_filters.DateFilter(field_name='date_of_birth', lookup_expr='lte')
    max_age = django_filters.DateFilter(field_name='date_of_birth', lookup_expr='gte')

    class Meta:
        model = BackGroundJobsProfile
        fields = ['gender', 'country', 'account_type', 'min_age', 'max_age']

class PropFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_for_rent = django_filters.BooleanFilter()
    is_for_sale = django_filters.BooleanFilter()
    material = django_filters.CharFilter(lookup_expr='icontains')
    used_in_movie = django_filters.CharFilter(lookup_expr='icontains')
    condition = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Prop
        fields = ['name', 'description', 'min_price', 'max_price', 'is_for_rent', 'is_for_sale', 'material', 'used_in_movie', 'condition']

class CostumeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_for_rent = django_filters.BooleanFilter()
    is_for_sale = django_filters.BooleanFilter()
    size = django_filters.CharFilter(lookup_expr='icontains')
    worn_by = django_filters.CharFilter(lookup_expr='icontains')
    era = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Costume
        fields = ['name', 'description', 'min_price', 'max_price', 'is_for_rent', 'is_for_sale', 'size', 'worn_by', 'era']

class LocationFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_for_rent = django_filters.BooleanFilter()
    is_for_sale = django_filters.BooleanFilter()
    address = django_filters.CharFilter(lookup_expr='icontains')
    min_capacity = django_filters.NumberFilter(field_name='capacity', lookup_expr='gte')
    is_indoor = django_filters.BooleanFilter()

    class Meta:
        model = Location
        fields = ['name', 'description', 'min_price', 'max_price', 'is_for_rent', 'is_for_sale', 'address', 'min_capacity', 'is_indoor']

class MemorabiliaFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_for_rent = django_filters.BooleanFilter()
    is_for_sale = django_filters.BooleanFilter()
    signed_by = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Memorabilia
        fields = ['name', 'description', 'min_price', 'max_price', 'is_for_rent', 'is_for_sale', 'signed_by']

class VehicleFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_for_rent = django_filters.BooleanFilter()
    is_for_sale = django_filters.BooleanFilter()
    make = django_filters.CharFilter(lookup_expr='icontains')
    model = django_filters.CharFilter(lookup_expr='icontains')
    min_year = django_filters.NumberFilter(field_name='year', lookup_expr='gte')
    max_year = django_filters.NumberFilter(field_name='year', lookup_expr='lte')

    class Meta:
        model = Vehicle
        fields = ['name', 'description', 'min_price', 'max_price', 'is_for_rent', 'is_for_sale', 'make', 'model', 'min_year', 'max_year']

class ArtisticMaterialFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_for_rent = django_filters.BooleanFilter()
    is_for_sale = django_filters.BooleanFilter()
    type = django_filters.CharFilter(lookup_expr='icontains')
    condition = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = ArtisticMaterial
        fields = ['name', 'description', 'min_price', 'max_price', 'is_for_rent', 'is_for_sale', 'type', 'condition']

class MusicItemFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_for_rent = django_filters.BooleanFilter()
    is_for_sale = django_filters.BooleanFilter()
    instrument_type = django_filters.CharFilter(lookup_expr='icontains')
    used_by = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = MusicItem
        fields = ['name', 'description', 'min_price', 'max_price', 'is_for_rent', 'is_for_sale', 'instrument_type', 'used_by']

class RareItemFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_for_rent = django_filters.BooleanFilter()
    is_for_sale = django_filters.BooleanFilter()
    provenance = django_filters.CharFilter(lookup_expr='icontains')
    is_one_of_a_kind = django_filters.BooleanFilter()

    class Meta:
        model = RareItem
        fields = ['name', 'description', 'min_price', 'max_price', 'is_for_rent', 'is_for_sale', 'provenance', 'is_one_of_a_kind']

class BandFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    band_type = django_filters.CharFilter(lookup_expr='iexact')
    location = django_filters.CharFilter(lookup_expr='icontains')
    min_members = django_filters.NumberFilter(method='filter_by_min_members')
    max_members = django_filters.NumberFilter(method='filter_by_max_members')
    
    def filter_by_min_members(self, queryset, name, value):
        """Filter bands that have at least the specified number of members"""
        return Band.with_counts(queryset).filter(_member_count__gte=value)
    
    def filter_by_max_members(self, queryset, name, value):
        """Filter bands that have at most the specified number of members"""
        return Band.with_counts(queryset).filter(_member_count__lte=value)

    class Meta:
        model = Band
        fields = ['name', 'band_type', 'location']
