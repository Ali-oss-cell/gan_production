from rest_framework import serializers
from .models import BackGroundJobsProfile, Item, Prop, Costume, Location, Memorabilia, Vehicle, ArtisticMaterial, MusicItem, RareItem

class BackGroundJobsSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BackGroundJobsProfile
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'country', 'date_of_birth', 'gender'
        ]
        
    def get_full_name(self, obj):
        """Combine first_name and last_name into a single field"""
        first_name = obj.user.first_name or ''
        last_name = obj.user.last_name or ''
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        return ""






class BackGroundJobs(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = BackGroundJobsProfile
        fields = [
            'id', 'email', 'username', 'country', 'date_of_birth', 'gender'
        ]
        extra_kwargs = {
            'user': {'read_only': True}  # User cannot be updated via this serializer
        }  
 


# Base serializer for Item-based models
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prop  # Using Prop as a concrete model that inherits from Item
        fields = [
            'id', 'name', 'description', 'price', 'genre', 'is_for_rent', 'is_for_sale',
            'created_at', 'updated_at', 'image'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def __init__(self, *args, **kwargs):
        # Dynamically set the model based on the context if provided
        if 'context' in kwargs and 'model' in kwargs['context']:
            self.Meta.model = kwargs['context']['model']
        super().__init__(*args, **kwargs)

# Serializer for the Prop model
class PropSerializer(ItemSerializer):
    class Meta(ItemSerializer.Meta):
        model = Prop
        fields = ItemSerializer.Meta.fields + ['material', 'used_in_movie', 'condition']

# Serializer for the Costume model
class CostumeSerializer(ItemSerializer):
    class Meta(ItemSerializer.Meta):
        model = Costume
        fields = ItemSerializer.Meta.fields + ['size', 'worn_by', 'era']

# Serializer for the Location model
class LocationSerializer(ItemSerializer):
    class Meta(ItemSerializer.Meta):
        model = Location
        fields = ItemSerializer.Meta.fields + ['address', 'capacity', 'is_indoor']

# Serializer for the Memorabilia model
class MemorabiliaSerializer(ItemSerializer):
    class Meta(ItemSerializer.Meta):
        model = Memorabilia
        fields = ItemSerializer.Meta.fields + ['signed_by', 'authenticity_certificate']

# Serializer for the Vehicle model
class VehicleSerializer(ItemSerializer):
    class Meta(ItemSerializer.Meta):
        model = Vehicle
        fields = ItemSerializer.Meta.fields + ['make', 'model', 'year']

# Serializer for the ArtisticMaterial model
class ArtisticMaterialSerializer(ItemSerializer):
    class Meta(ItemSerializer.Meta):
        model = ArtisticMaterial
        fields = ItemSerializer.Meta.fields + ['type', 'condition']

# Serializer for the MusicItem model
class MusicItemSerializer(ItemSerializer):
    class Meta(ItemSerializer.Meta):
        model = MusicItem
        fields = ItemSerializer.Meta.fields + ['instrument_type', 'used_by']

# Serializer for the RareItem model
class RareItemSerializer(ItemSerializer):
    class Meta(ItemSerializer.Meta):
        model = RareItem
        fields = ItemSerializer.Meta.fields + ['provenance', 'is_one_of_a_kind']



