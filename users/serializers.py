from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import date
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import os

User = get_user_model()

# List of known disposable email domains
DISPOSABLE_EMAIL_DOMAINS = {
    'mailinator.com', 'temp-mail.org', 'guerrillamail.com',
    '10minutemail.com', 'throwawaymail.com', 'tempmail.com',
    'fakeinbox.com', 'trashmail.com', 'maildrop.cc'
}

class UnifiedUserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=[('talent', 'Talent'), ('background', 'Background Job'), ('dashboard', 'Dashboard User'), ('admin_dashboard', 'Admin Dashboard User')],
        write_only=True
    )
    gender = serializers.ChoiceField(
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other'), ('Prefer not to say', 'Prefer not to say')],
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 'role',
            'country', 'date_of_birth', 'gender'
        ]
        extra_kwargs = {
            'email': {'validators': []},  # Disable default uniqueness check
            'password': {'write_only': True},
            'date_of_birth': {'write_only': True}
        }
    
    
  # Raises ValidationError if email is disposable        return value
    def validate(self, data):
        # Validate required fields
        required_fields = [
            'country', 
            'date_of_birth', 'gender', 'role'
        ]
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(
                    {field: "This field is required."}
                )

        # Age validation
        dob = data['date_of_birth']
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise serializers.ValidationError({
                'date_of_birth': 'You must be at least 18 years old.'
            })

        return data

    def validate_email(self, value):
        domain = value.split('@')[-1].lower()
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            raise serializers.ValidationError("Disposable email addresses are not allowed.")
        return value

    def create(self, validated_data):
        role = validated_data.pop('role')
        gender = validated_data.pop('gender')

        if role == 'talent':
            user = User.objects.create_talent_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                country=validated_data['country'],
                date_of_birth=validated_data['date_of_birth'],
                gender=gender
            )
        elif role == 'background':
            user = User.objects.create_background_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                country=validated_data['country'],
                date_of_birth=validated_data['date_of_birth'],
                gender=gender
            )
        elif role == 'dashboard':
            user = User.objects.create_dashboard_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                country=validated_data['country'],
                date_of_birth=validated_data['date_of_birth'],
                gender=gender
            )
        elif role == 'admin_dashboard':
            user = User.objects.create_admin_dashboard_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                country=validated_data['country'],
                date_of_birth=validated_data['date_of_birth'],
                gender=gender
            )
        
        # Generate verification token
        import secrets
        from django.utils import timezone
        user.email_verification_token = secrets.token_urlsafe(32)
        user.email_verification_token_created = timezone.now()
        user.save()

        # Send verification email
        from django.core.mail import send_mail
        from django.conf import settings
        
        try:
            # Get the frontend URL from environment variables, fallback to localhost for development
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            verification_url = f"{frontend_url}/verify-email?token={user.email_verification_token}"
            
            send_mail(
                'Verify your email address',
                f'Please click the following link to verify your email address: {verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            print(f"DEBUG: Verification email sent to {user.email}")
        except Exception as e:
            print(f"DEBUG: Email sending failed for {user.email}: {e}")
            # Don't fail registration if email sending fails
            
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            'is_talent': self.user.is_talent,
            'is_background': self.user.is_background,
            'is_dashboard': self.user.is_dashboard,
            'is_staff': self.user.is_staff
        })
        return data

class TalentLoginSerializer(CustomTokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_talent:
            raise serializers.ValidationError("This account is not registered as Talent.")
        return data

class BackGroundJobsLoginSerializer(CustomTokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_background:
            raise serializers.ValidationError("This account is not registered as Background.")
        return data

class DashboardLoginSerializer(CustomTokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_dashboard:
            raise serializers.ValidationError("This account is not registered as Dashboard user.")
        return data

class AdminDashboardLoginSerializer(CustomTokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_dashboard or not self.user.is_dashboard_admin:
            raise serializers.ValidationError("This account is not registered as Admin Dashboard user.")
        return data