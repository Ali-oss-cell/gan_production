from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from users.managers import BaseUserManager


class BaseUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_token_created = models.DateTimeField(null=True, blank=True)
    
    # Role flags
    is_talent = models.BooleanField(default=False)
    is_background = models.BooleanField(default=False)
    is_dashboard = models.BooleanField(default=False)
    is_dashboard_admin = models.BooleanField(default=False)

    # Stripe customer ID
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)

    # Common basic fields with proper defaults
    country = models.CharField(max_length=25, blank=True)
    city = models.CharField(max_length=25, blank=True)
    zipcode = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(default=timezone.now)  # Valid default
    
    # Add gender field
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say')
    ]
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)

    objects = BaseUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email