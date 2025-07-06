from django.contrib.auth.models import BaseUserManager as DjangoBaseUserManager
from django.db import transaction

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

    @transaction.atomic
    def create_talent_user(self, email, password=None, **extra_fields):
        gender = extra_fields.pop('gender', 'Prefer not to say')
        country = extra_fields.pop('country', 'country')
        date_of_birth = extra_fields.pop('date_of_birth', None)
        
        try:
            # Check if user exists
            user = self.get(email=email)
            # Update existing user
            if not user.is_talent:
                user.is_talent = True
                user.gender = gender
                user.save(update_fields=['is_talent', 'gender'])
        except self.model.DoesNotExist:
            # Create new user with profile fields
            user = self.create_user(
                email=email,
                password=password,
                is_talent=True,
                gender=gender,
                **extra_fields
            )
        
        # Import here to avoid circular import
        from profiles.models import TalentUserProfile
        
        # Create or update profile with better error handling
        try:
            # Try to get existing profile first
            profile = TalentUserProfile.objects.get(user=user)
            # Update existing profile
            profile.country = country
            profile.date_of_birth = date_of_birth
            profile.save(update_fields=['country', 'date_of_birth'])
        except TalentUserProfile.DoesNotExist:
            # Create new profile
            try:
                TalentUserProfile.objects.create(
                    user=user,
                    country=country,
                    date_of_birth=date_of_birth
                )
            except Exception as e:
                # If profile creation fails, log it but don't fail the user creation
                print(f"DEBUG: Profile creation failed for {user.email}: {e}")
                # Create minimal profile
                TalentUserProfile.objects.create(user=user)
        except Exception as e:
            print(f"DEBUG: Profile update failed for {user.email}: {e}")
            
        return user

    @transaction.atomic
    def create_background_user(self, email, password=None, **extra_fields):
        gender = extra_fields.pop('gender', 'Prefer not to say')
        country = extra_fields.pop('country', 'country')
        date_of_birth = extra_fields.pop('date_of_birth', None)
        
        try:
            # Check if user exists
            user = self.get(email=email)
            # Update existing user
            if not user.is_background:
                user.is_background = True
                user.gender = gender
                user.save(update_fields=['is_background', 'gender'])
        except self.model.DoesNotExist:
            # Create new user with profile fields
            user = self.create_user(
                email=email,
                password=password,
                is_background=True,
                gender=gender,
                **extra_fields
            )
        
        # Import here to avoid circular import
        from profiles.models import BackGroundJobsProfile
        
        # Create or update background profile with better error handling
        try:
            # Try to get existing profile first
            profile = BackGroundJobsProfile.objects.get(user=user)
            # Update existing profile
            profile.country = country
            profile.date_of_birth = date_of_birth
            profile.save(update_fields=['country', 'date_of_birth'])
        except BackGroundJobsProfile.DoesNotExist:
            # Create new profile
            try:
                BackGroundJobsProfile.objects.create(
                    user=user,
                    country=country,
                    date_of_birth=date_of_birth
                )
            except Exception as e:
                # If profile creation fails, log it but don't fail the user creation
                print(f"DEBUG: Background profile creation failed for {user.email}: {e}")
                # Create minimal profile
                BackGroundJobsProfile.objects.create(user=user)
        except Exception as e:
            print(f"DEBUG: Background profile update failed for {user.email}: {e}")
            
        return user
        
    @transaction.atomic
    def create_dashboard_user(self, email, password=None, **extra_fields):
        gender = extra_fields.pop('gender', 'Prefer not to say')
        country = extra_fields.pop('country', 'country')
        date_of_birth = extra_fields.pop('date_of_birth', None)
        try:
            user = self.get(email=email)
            if not user.is_dashboard:
                user.is_dashboard = True
                user.is_dashboard_admin = False
                user.gender = gender
                user.save(update_fields=['is_dashboard', 'is_dashboard_admin', 'gender'])
        except self.model.DoesNotExist:
            user = self.create_user(
                email=email,
                password=password,
                is_dashboard=True,
                is_dashboard_admin=False,
                gender=gender,
                **extra_fields
            )
        return user
        
    @transaction.atomic
    def create_admin_dashboard_user(self, email, password=None, **extra_fields):
        gender = extra_fields.pop('gender', 'Prefer not to say')
        country = extra_fields.pop('country', 'country')
        date_of_birth = extra_fields.pop('date_of_birth', None)
        try:
            user = self.get(email=email)
            if not user.is_dashboard or not user.is_dashboard_admin:
                user.is_dashboard = True
                user.is_dashboard_admin = True
                user.gender = gender
                user.save(update_fields=['is_dashboard', 'is_dashboard_admin', 'gender'])
        except self.model.DoesNotExist:
            user = self.create_user(
                email=email,
                password=password,
                is_dashboard=True,
                is_dashboard_admin=True,
                gender=gender,
                **extra_fields
            )
        return user