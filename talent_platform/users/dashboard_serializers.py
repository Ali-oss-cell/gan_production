from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class DashboardUserRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'first_name', 'last_name']
    
    def validate(self, data):
        # Check that passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return data
    
    def create(self, validated_data):
        # Remove confirm_password from validated data
        validated_data.pop('confirm_password')
        
        # Create a unique email from username
        username = validated_data.pop('username')
        email = f"{username}@dashboard.internal"
        
        # Check if username (email) already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})
        
        # Create regular dashboard user (not admin)
        user = User.objects.create_dashboard_user(
            email=email,
            password=validated_data.pop('password'),
            **validated_data
        )
        
        return user

class DashboardUsernameLoginSerializer(TokenObtainPairSerializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        # Convert username to email format
        email = f"{attrs.pop('username')}@dashboard.internal"
        attrs['email'] = email
        
        # Call parent validation
        data = super().validate(attrs)
        
        # Check if user is a dashboard user
        if not self.user.is_dashboard:
            raise serializers.ValidationError("This account is not registered as a Dashboard user.")
        
        # Add user role information
        data.update({
            'is_dashboard': self.user.is_dashboard,
            'is_staff': self.user.is_staff,
            'username': self.user.email.split('@')[0]  # Extract username from email
        })
        
        return data

class AdminDashboardUsernameLoginSerializer(DashboardUsernameLoginSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Check if user is an admin dashboard user
        if not self.user.is_staff:
            raise serializers.ValidationError("This account is not registered as an Admin Dashboard user.")
        
        return data