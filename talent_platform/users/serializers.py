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

def send_verification_email_sync(user_email, verification_url):
    """
    Synchronous email sending function with error handling
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        send_mail(
            'Verify your email address',
            f'Please click the following link to verify your email address: {verification_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        logger.info(f"Verification email sent to {user_email}")
        return True
    except Exception as e:
        logger.error(f"Email sending failed for {user_email}: {str(e)}")
        return False

def send_verification_email_async(user_email, verification_url):
    """
    Asynchronous email sending with Celery fallback
    """
    try:
        # Try to use Celery if available
        from celery import current_app
        if current_app.control.inspect().active():
            send_verification_email_task.delay(user_email, verification_url)
            logger.info(f"Queued verification email for {user_email}")
            return True
    except Exception as e:
        logger.warning(f"Celery not available, falling back to sync email: {str(e)}")
    
    # Fallback to synchronous sending
    return send_verification_email_sync(user_email, verification_url)

# Celery tasks (optional - only works if Celery is configured)
try:
    from celery import shared_task
    
    @shared_task
    def send_verification_email_task(user_email, verification_url):
        """
        Celery task for sending verification emails
        """
        return send_verification_email_sync(user_email, verification_url)
    
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
            
            # Generate verification token only if user is not already verified
            self._generate_verification_token(user)
            
            # Queue email sending only if user is not already verified
            if not user.email_verified:
                self._queue_verification_email(user)
            
            logger.info(f"Successfully created user {user.email} with role {role}")
            return user
            
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            raise serializers.ValidationError({'detail': f'User creation failed: {str(e)}'})

    def _generate_verification_token(self, user):
        """
        Generate email verification token only if user is not already verified
        """
        try:
            # If user is already verified, don't generate a new token
            if user.email_verified:
                logger.info(f"User {user.email} is already verified, skipping token generation")
                return
            
            import secrets
            from django.utils import timezone
            
            user.email_verification_token = secrets.token_urlsafe(32)
            user.email_verification_token_created = timezone.now()
            user.last_verification_email_sent = timezone.now()
            user.save(update_fields=['email_verification_token', 'email_verification_token_created', 'last_verification_email_sent'])
            
            logger.info(f"Generated verification token for {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to generate verification token for {user.email}: {str(e)}")
            # Don't raise exception - user creation should succeed even if token generation fails

    def _send_verification_email_async(self, user):
        """
        Send verification email asynchronously (non-blocking)
        """
        try:
            backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
            verification_url = f"{backend_url}/api/verify-email/?token={user.email_verification_token}"
            
            # Try async first, fallback to sync
            success = send_verification_email_async(user.email, verification_url)
            
            if success:
                logger.info(f"Verification email queued for {user.email}")
            else:
                logger.warning(f"Failed to queue verification email for {user.email}")
                
        except Exception as e:
            logger.error(f"Email sending process failed for {user.email}: {str(e)}")
            # Don't raise exception - user creation should succeed even if email fails

    def _send_verification_email(self, user):
        """
        Send verification email with fallback handling (legacy method)
        """
        try:
            backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
            verification_url = f"{backend_url}/api/verify-email/?token={user.email_verification_token}"
            
            # Try async first, fallback to sync
            success = send_verification_email_async(user.email, verification_url)
            
            if success:
                logger.info(f"Verification email sent for {user.email}")
            else:
                logger.warning(f"Failed to send verification email for {user.email}")
                
        except Exception as e:
            logger.error(f"Email sending process failed for {user.email}: {str(e)}")
            # Don't raise exception - user creation should succeed even if email fails

    def _queue_verification_email(self, user):
        """
        Queue verification email for background processing (truly non-blocking)
        """
        try:
            import threading
            
            # Run email sending in a separate thread to avoid blocking registration
            def send_email_background():
                try:
                    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
                    verification_url = f"{frontend_url}/verify-email?token={user.email_verification_token}"
                    
                    # Use simple background sending
                    send_verification_email_sync(user.email, verification_url)
                    logger.info(f"Background verification email sent for {user.email}")
                except Exception as e:
                    logger.warning(f"Background email sending failed for {user.email}: {str(e)}")
            
            # Start background thread
            email_thread = threading.Thread(target=send_email_background, daemon=True)
            email_thread.start()
            
            logger.info(f"Queued verification email for background sending: {user.email}")
            
        except Exception as e:
            logger.warning(f"Failed to queue verification email for {user.email}: {str(e)}")
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