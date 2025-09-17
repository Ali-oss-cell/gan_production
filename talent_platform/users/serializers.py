from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import date
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import os
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

# List of known disposable email domains
DISPOSABLE_EMAIL_DOMAINS = {
    'mailinator.com', 'temp-mail.org', 'guerrillamail.com',
    '10minutemail.com', 'throwawaymail.com', 'tempmail.com',
    'fakeinbox.com', 'trashmail.com', 'maildrop.cc'
}


def send_verification_code_email(user_email, verification_code):
    """
    Send verification code email (no links, just code)
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = 'Your Email Verification Code'
        message = f"""
Hi there!

Thank you for registering with Gan7Club.

Your email verification code is: {verification_code}

Please enter this code on the verification page to complete your registration.

This code will expire in 24 hours.

If you didn't create this account, you can safely ignore this email.

Best regards,
The Gan7Club Team
        """.strip()
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        logger.info(f"Verification code email sent to {user_email}")
        return True
    except Exception as e:
        logger.error(f"Verification code email failed for {user_email}: {str(e)}")
        return False


# Celery tasks (optional - only works if Celery is configured)
try:
    from celery import shared_task
    
    @shared_task
    def send_verification_code_task(user_email, verification_code):
        """
        Celery task for sending verification codes
        """
        return send_verification_code_email(user_email, verification_code)
    
    @shared_task
    def create_talent_profile_task(user_id, country, date_of_birth):
        """
        Celery task for creating talent profiles asynchronously
        """
        try:
            from django.contrib.auth import get_user_model
            from profiles.models import TalentUserProfile
            
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            TalentUserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'country': country or '',
                    'date_of_birth': date_of_birth
                }
            )
            logger.info(f"Created talent profile for user {user.email} via Celery")
            return True
        except Exception as e:
            logger.error(f"Failed to create talent profile via Celery: {str(e)}")
            return False
    
    @shared_task
    def create_background_profile_task(user_id, country, date_of_birth):
        """
        Celery task for creating background profiles asynchronously
        """
        try:
            from django.contrib.auth import get_user_model
            from profiles.models import BackGroundJobsProfile
            
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            BackGroundJobsProfile.objects.get_or_create(
                user=user,
                defaults={
                    'country': country or '',
                    'date_of_birth': date_of_birth
                }
            )
            logger.info(f"Created background profile for user {user.email} via Celery")
            return True
        except Exception as e:
            logger.error(f"Failed to create background profile via Celery: {str(e)}")
            return False
        
except ImportError:
    logger.warning("Celery not installed, email sending and profile creation will be synchronous")

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
    
    def validate(self, data):
        """
        Optimized validation with reduced database queries
        """
        try:
            # Validate required fields
            required_fields = ['country', 'date_of_birth', 'gender', 'role']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(
                        {field: "This field is required."}
                    )
                
                # Additional validation for country field
                if field == 'country' and data.get(field):
                    country = data[field].strip()
                    if not country or len(country) < 2:
                        raise serializers.ValidationError({
                            'country': 'Country must be at least 2 characters long.'
                        })
                    data[field] = country

            # Parse date_of_birth if it's a string
            if isinstance(data['date_of_birth'], str):
                try:
                    from datetime import datetime
                    parsed_date = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
                    data['date_of_birth'] = parsed_date
                except ValueError:
                    raise serializers.ValidationError({
                        'date_of_birth': 'Invalid date format. Use YYYY-MM-DD format.'
                    })

            # Age validation
            dob = data['date_of_birth']
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise serializers.ValidationError({
                    'date_of_birth': 'You must be at least 18 years old.'
                })

            # Email uniqueness check - moved to create() method to avoid duplicate queries
            # This will be handled in the manager methods

            return data
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            raise

    def validate_date_of_birth(self, value):
        """
        Validate and parse date_of_birth field
        """
        try:
            if isinstance(value, str):
                from datetime import datetime
                parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
                return parsed_date
            elif isinstance(value, date):
                return value
            else:
                raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD format.")
        except ValueError:
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD format.")
        except Exception as e:
            logger.error(f"Date of birth validation error: {str(e)}")
            raise serializers.ValidationError("Invalid date format.")

    def validate_email(self, value):
        """
        Validate email format and check against disposable domains
        """
        try:
            domain = value.split('@')[-1].lower()
            if domain in DISPOSABLE_EMAIL_DOMAINS:
                raise serializers.ValidationError("Disposable email addresses are not allowed.")
            return value
        except Exception as e:
            logger.error(f"Email validation error: {str(e)}")
            raise

    def create(self, validated_data):
        """
        Optimized user creation with async email sending
        """
        try:
            role = validated_data.pop('role')
            gender = validated_data.pop('gender')
            
            # Create user based on role
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
            else:
                raise serializers.ValidationError({'role': 'Invalid role specified.'})
            
            # Generate verification code only if user is not already verified
            self._generate_verification_code(user)
            
            # Queue email sending only if user is not already verified
            if not user.email_verified:
                self._queue_verification_email(user)
            
            logger.info(f"Successfully created user {user.email} with role {role}")
            return user
            
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            raise serializers.ValidationError({'detail': f'User creation failed: {str(e)}'})

    def _generate_verification_code(self, user):
        """
        Generate email verification code only if user is not already verified
        """
        try:
            # If user is already verified, don't generate a new code
            if user.email_verified:
                logger.info(f"User {user.email} is already verified, skipping code generation")
                return
            
            import random
            from django.utils import timezone
            
            # Generate 6-digit verification code
            verification_code = str(random.randint(100000, 999999))
            
            user.email_verification_code = verification_code
            user.email_verification_code_created = timezone.now()
            user.last_verification_email_sent = timezone.now()
            user.save(update_fields=['email_verification_code', 'email_verification_code_created', 'last_verification_email_sent'])
            
            logger.info(f"Generated verification code for {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to generate verification code for {user.email}: {str(e)}")
            # Don't raise exception - user creation should succeed even if code generation fails


    def _queue_verification_email(self, user):
        """
        Queue verification email for background processing (truly non-blocking)
        """
        try:
            import threading
            
            # Run email sending in a separate thread to avoid blocking registration
            def send_email_background():
                try:
                    logger.info(f"Sending verification code to {user.email}")
                    
                    # Send verification code email
                    send_verification_code_email(user.email, user.email_verification_code)
                    logger.info(f"Background verification code sent for {user.email}")
                except Exception as e:
                    logger.error(f"Background email sending failed for {user.email}: {str(e)}")
            
            # Start background thread
            email_thread = threading.Thread(target=send_email_background, daemon=True)
            email_thread.start()
            
            logger.info(f"Queued verification code email for background sending: {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to queue verification email for {user.email}: {str(e)}")
            # Don't raise exception - user creation should succeed even if email fails

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_talent': self.user.is_talent,
            'is_background': self.user.is_background,
            'is_dashboard': self.user.is_dashboard,
            'is_dashboard_admin': self.user.is_dashboard_admin,
            'is_staff': self.user.is_staff,
            'email_verified': self.user.email_verified
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