from django.contrib.auth.models import BaseUserManager as DjangoBaseUserManager
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class BaseUserManager(DjangoBaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

    def create_talent_user(self, email, password=None, **extra_fields):
        """
        Optimized talent user creation with reduced database queries
        """
        try:
            # Extract profile fields
            gender = extra_fields.pop('gender', 'Prefer not to say')
            country = extra_fields.pop('country', '')
            residency = extra_fields.pop('residency', '')
            date_of_birth = extra_fields.pop('date_of_birth', None)
            
            # Use get_or_create to avoid separate exists() and get() calls
            user, created = self.get_or_create(
                email=email,
                defaults={
                    'password': password,
                    'is_talent': True,
                    'gender': gender,
                    'country': country,
                    'residency': residency,
                    'date_of_birth': date_of_birth,
                    **extra_fields
                }
            )
            
            if not created:
                # User exists, update if needed
                if not user.is_talent:
                    user.is_talent = True
                    user.gender = gender
                    user.country = country
                    # Handle residency field safely
                    try:
                        user.residency = residency
                        user.save(update_fields=['is_talent', 'gender', 'country', 'residency', 'date_of_birth'])
                    except AttributeError:
                        # Residency field doesn't exist in database yet, skip it
                        user.save(update_fields=['is_talent', 'gender', 'country', 'date_of_birth'])
                    logger.info(f"Updated existing user {email} to talent")
            else:
                # New user created, set password
                user.set_password(password)
                user.save(update_fields=['password'])
                
                # Create profile asynchronously (non-blocking)
                self._create_talent_profile_async(user, country, date_of_birth)
                logger.info(f"Created new talent user {email}")
            
            return user

        except Exception as e:
            logger.error(f"Error creating talent user {email}: {str(e)}")
            raise

    def create_background_user(self, email, password=None, **extra_fields):
        """
        Create a background user with simplified logic
        """
        try:
            # Extract profile fields
            gender = extra_fields.pop('gender', 'Prefer not to say')
            country = extra_fields.pop('country', '')
            residency = extra_fields.pop('residency', '')
            date_of_birth = extra_fields.pop('date_of_birth', None)
            
            # Check if user already exists
            if self.filter(email=email).exists():
                existing_user = self.get(email=email)
                if not existing_user.is_background:
                    existing_user.is_background = True
                    existing_user.gender = gender
                    existing_user.country = country
                    # Handle residency field safely
                    try:
                        existing_user.residency = residency
                        existing_user.date_of_birth = date_of_birth
                        existing_user.save()
                    except AttributeError:
                        # Residency field doesn't exist in database yet, skip it
                        existing_user.date_of_birth = date_of_birth
                        existing_user.save()
                    logger.info(f"Updated existing user {email} to background")
                return existing_user
            
            # Create new user
            user = self.create_user(
                email=email,
                password=password,
                is_background=True,
                gender=gender,
                country=country,
                residency=residency,
                date_of_birth=date_of_birth,
                **extra_fields
            )
        
            # Create profile separately with error handling
            self._create_background_profile(user, country, date_of_birth)
            
            logger.info(f"Created new background user {email}")
            return user
        
        except Exception as e:
            logger.error(f"Error creating background user {email}: {str(e)}")
            raise

    def create_dashboard_user(self, email, password=None, **extra_fields):
        """
        Create a dashboard user with simplified logic
        """
        try:
            # Extract profile fields
            gender = extra_fields.pop('gender', 'Prefer not to say')
            country = extra_fields.pop('country', '')
            residency = extra_fields.pop('residency', '')
            date_of_birth = extra_fields.pop('date_of_birth', None)
            
            # Check if user already exists
            if self.filter(email=email).exists():
                existing_user = self.get(email=email)
                if not existing_user.is_dashboard:
                    existing_user.is_dashboard = True
                    existing_user.is_dashboard_admin = False
                    existing_user.gender = gender
                    existing_user.country = country
                    # Handle residency field safely
                    try:
                        existing_user.residency = residency
                        existing_user.date_of_birth = date_of_birth
                        existing_user.save()
                    except AttributeError:
                        # Residency field doesn't exist in database yet, skip it
                        existing_user.date_of_birth = date_of_birth
                        existing_user.save()
                    logger.info(f"Updated existing user {email} to dashboard")
                return existing_user
            
            # Create new user
            user = self.create_user(
                email=email,
                password=password,
                is_dashboard=True,
                is_dashboard_admin=False,
                gender=gender,
                country=country,
                residency=residency,
                date_of_birth=date_of_birth,
                **extra_fields
            )
            
            logger.info(f"Created new dashboard user {email}")
            return user
        
        except Exception as e:
            logger.error(f"Error creating dashboard user {email}: {str(e)}")
            raise

    def create_admin_dashboard_user(self, email, password=None, **extra_fields):
        """
        Create an admin dashboard user with simplified logic
        """
        try:
            # Extract profile fields
            gender = extra_fields.pop('gender', 'Prefer not to say')
            country = extra_fields.pop('country', '')
            residency = extra_fields.pop('residency', '')
            date_of_birth = extra_fields.pop('date_of_birth', None)
            
            # Check if user already exists
            if self.filter(email=email).exists():
                existing_user = self.get(email=email)
                if not existing_user.is_dashboard or not existing_user.is_dashboard_admin:
                    existing_user.is_dashboard = True
                    existing_user.is_dashboard_admin = True
                    existing_user.gender = gender
                    existing_user.country = country
                    # Handle residency field safely
                    try:
                        existing_user.residency = residency
                        existing_user.date_of_birth = date_of_birth
                        existing_user.save()
                    except AttributeError:
                        # Residency field doesn't exist in database yet, skip it
                        existing_user.date_of_birth = date_of_birth
                        existing_user.save()
                    logger.info(f"Updated existing user {email} to admin dashboard")
                return existing_user
            
            # Create new user
            user = self.create_user(
                email=email,
                password=password,
                is_dashboard=True,
                is_dashboard_admin=True,
                gender=gender,
                country=country,
                residency=residency,
                date_of_birth=date_of_birth,
                **extra_fields
            )
            
            logger.info(f"Created new admin dashboard user {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating admin dashboard user {email}: {str(e)}")
            raise

    def _create_talent_profile_async(self, user, country, date_of_birth):
        """
        Create talent profile asynchronously (non-blocking)
        """
        try:
            # Try to use Celery if available for async profile creation
            try:
                from celery import current_app
                from .serializers import create_talent_profile_task
                if current_app.control.inspect().active():
                    create_talent_profile_task.delay(user.id, country, date_of_birth)
                    logger.info(f"Queued talent profile creation for user {user.email}")
                    return
            except Exception:
                pass
            
            # Fallback to synchronous creation
            self._create_talent_profile(user, country, date_of_birth)
            
        except Exception as e:
            logger.warning(f"Failed to create talent profile for {user.email}: {str(e)}")

    def _create_talent_profile(self, user, country, date_of_birth):
        """
        Create talent profile with error handling (synchronous fallback)
        """
        try:
            from profiles.models import TalentUserProfile
            TalentUserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'country': country or '',
                    'city': '',  # Initialize with empty string
                    'phone': '',  # Initialize with empty string
                    'gender': 'Male',  # Initialize with default value
                    'date_of_birth': date_of_birth
                }
            )
            logger.info(f"Created talent profile for user {user.email}")
        except Exception as e:
            logger.warning(f"Failed to create talent profile for {user.email}: {str(e)}")
            # Don't raise exception - user creation should succeed even if profile fails

    def _create_background_profile(self, user, country, date_of_birth):
        """
        Create background profile with error handling
        """
        try:
            from profiles.models import BackGroundJobsProfile
            BackGroundJobsProfile.objects.get_or_create(
                user=user,
                defaults={
                    'country': country or '',
                    'date_of_birth': date_of_birth
                }
            )
            logger.info(f"Created background profile for user {user.email}")
        except Exception as e:
            logger.warning(f"Failed to create background profile for {user.email}: {str(e)}")
            # Don't raise exception - user creation should succeed even if profile fails