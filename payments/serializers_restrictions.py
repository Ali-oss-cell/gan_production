from rest_framework import serializers
from .models_restrictions import RestrictedCountryUser
from dashboard.serializers import UserBasicSerializer

class RestrictedCountryUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the RestrictedCountryUser model.
    Includes user details and account management fields.
    """
    user = UserBasicSerializer(read_only=True)
    last_updated_by = UserBasicSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = RestrictedCountryUser
        fields = ['id', 'user', 'user_id', 'country', 'is_approved', 'account_type', 
                  'notes', 'created_at', 'updated_at', 'last_updated_by']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        # Remove user_id from validated_data if present
        validated_data.pop('user_id', None)
        
        # Set last_updated_by to the current user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            instance.last_updated_by = request.user
        
        return super().update(instance, validated_data)