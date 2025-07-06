from django.contrib.auth.models import BaseUserManager as DjangoBaseUserManager
from django.db import transaction
import signal
import time

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Profile creation timed out")

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

    def _create_profile_with_raw_sql(self, user, country, date_of_birth):
        """
        Create TalentUserProfile using raw SQL to bypass Django ORM issues
        """
        from django.db import connection
        
        print(f"DEBUG: Creating profile via raw SQL for {user.email}")
        start_time = time.time()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO profiles_talentuserprofile 
                    (user_id, is_verified, profile_complete, account_type, country, city, zipcode, phone, gender, date_of_birth)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [user.id, False, False, 'free', country or 'US', 'city', '', '', 'Male', date_of_birth])
                
                profile_id = cursor.fetchone()[0]
                end_time = time.time()
                print(f"DEBUG: Profile created via raw SQL in {end_time - start_time:.2f}s with ID: {profile_id}")
                
                # Return the profile instance
                from profiles.models import TalentUserProfile
                return TalentUserProfile.objects.get(id=profile_id)
                
        except Exception as e:
            end_time = time.time()
            print(f"DEBUG: Raw SQL profile creation failed after {end_time - start_time:.2f}s: {e}")
            raise

    def _create_profile_with_timeout(self, user, country, date_of_birth, timeout_seconds=5):
        """
        Create TalentUserProfile with timeout protection - but try raw SQL first
        """
        # Try raw SQL first since it's faster and bypasses Django ORM issues
        print(f"DEBUG: Attempting raw SQL profile creation for {user.email}")
        try:
            return self._create_profile_with_raw_sql(user, country, date_of_birth)
        except Exception as e:
            print(f"DEBUG: Raw SQL failed, trying Django ORM with timeout: {e}")
            
            # Import here to avoid circular import
            from profiles.models import TalentUserProfile
            
            # Only use timeout as last resort
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                print(f"DEBUG: Attempting Django ORM profile creation for {user.email}")
                start_time = time.time()
                
                profile = TalentUserProfile.objects.create(
                    user=user,
                    country=country,
                    date_of_birth=date_of_birth
                )
                
                end_time = time.time()
                print(f"DEBUG: Django ORM profile created in {end_time - start_time:.2f}s")
                return profile
                
            except TimeoutError:
                print(f"DEBUG: Django ORM profile creation timed out for {user.email}")
                raise Exception("Profile creation timed out")
            except Exception as e:
                print(f"DEBUG: Django ORM profile creation failed: {e}")
                raise
            finally:
                signal.alarm(0)  # Cancel the alarm
                signal.signal(signal.SIGALRM, old_handler)  # Restore old handler

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
            # Create new profile - use raw SQL first
            try:
                profile = self._create_profile_with_timeout(user, country, date_of_birth)
                print(f"DEBUG: Profile successfully created for {user.email}")
            except Exception as e:
                print(f"DEBUG: All profile creation methods failed for {user.email}: {e}")
                # Don't fail the user creation - let them complete registration without profile
                # They can create the profile later
                print(f"DEBUG: User {user.email} created successfully without profile")
                pass
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