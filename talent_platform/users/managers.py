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
        country = extra_fields.pop('country', 'country')  # Add this line
        date_of_birth = extra_fields.pop('date_of_birth', None)  # Add this line
        
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
        
        # Update profile with additional fields
        from profiles.models import TalentUserProfile
        TalentUserProfile.objects.update_or_create(
            user=user,
            defaults={
                'country': country,  # Add this
                'date_of_birth': date_of_birth  # Add this
            }
        )
        return user

    @transaction.atomic
    def create_background_user(self, email, password=None, **extra_fields):
        gender = extra_fields.pop('gender', 'Prefer not to say')
        country = extra_fields.pop('country', 'country')  # Add this
        date_of_birth = extra_fields.pop('date_of_birth', None)  # Add this
        
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
        
        # Update background profile
        from profiles.models import BackGroundJobsProfile
        BackGroundJobsProfile.objects.update_or_create(
            user=user,
            defaults={
                'country': country,  # Add this
                'date_of_birth': date_of_birth  # Add this
            }
        )
        return user
        
    @transaction.atomic
    def create_dashboard_user(self, email, password=None, **extra_fields):
        gender = extra_fields.pop('gender', 'Prefer not to say')
        country = extra_fields.pop('country', 'country')
        date_of_birth = extra_fields.pop('date_of_birth', None)
        
        try:
            # Check if user exists
            user = self.get(email=email)
            # Update existing user
            if not user.is_dashboard:
                user.is_dashboard = True
                user.gender = gender
                user.save(update_fields=['is_dashboard', 'gender'])
        except self.model.DoesNotExist:
            # Create new user with profile fields
            user = self.create_user(
                email=email,
                password=password,
                is_dashboard=True,
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
            # Check if user exists
            user = self.get(email=email)
            # Update existing user
            if not user.is_dashboard or not user.is_staff:
                user.is_dashboard = True
                user.is_staff = True
                user.gender = gender
                user.save(update_fields=['is_dashboard', 'is_staff', 'gender'])
        except self.model.DoesNotExist:
            # Create new user with profile fields
            user = self.create_user(
                email=email,
                password=password,
                is_dashboard=True,
                is_staff=True,  # Admin dashboard users have staff privileges
                gender=gender,
                **extra_fields
            )
        
        return user