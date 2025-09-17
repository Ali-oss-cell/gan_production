from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from .serializers import UnifiedUserSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import TalentLoginSerializer, BackGroundJobsLoginSerializer, DashboardLoginSerializer, AdminDashboardLoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from .models import BaseUser
from .permissions import IsAdminDashboardUser
import logging
import json
import os

logger = logging.getLogger(__name__)

class UserRegistrationView(APIView):
    """
    Optimized registration endpoint for all user types with improved performance
    """
    def post(self, request):
        try:
            logger.info(f"Registration attempt for email: {request.data.get('email', 'unknown')}")
            
            # Validate request data
            serializer = UnifiedUserSerializer(data=request.data)
            
            if not serializer.is_valid():
                logger.warning(f"Registration validation failed: {serializer.errors}")
                return Response({
                    'success': False,
                    'message': 'Registration validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create user with optimized process
            user = serializer.save()
            
            # Prepare success response immediately (don't wait for email)
            response_data = {
                'success': True,
                'message': 'User registered successfully',
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'roles': {
                        'is_talent': user.is_talent,
                        'is_background': user.is_background,
                        'is_dashboard': user.is_dashboard,
                        'is_dashboard_admin': user.is_dashboard_admin
                    }
                },
                'email_verification': {
                    'required': True,
                    'message': 'Please check your email for verification link'
                }
            }
            
            logger.info(f"User registration successful for {user.email}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Registration failed with exception: {str(e)}")
            return Response({
                'success': False,
                'message': 'Registration failed due to server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BaseLoginView(TokenObtainPairView):
    def get_user(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.user

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            
            # Get the user from the validated data
            user = self.get_user(request)
            
            # Check email verification status
            if not user.email_verified:
                response.data['message'] = 'Your email is not verified. You can still use your account, but we recommend verifying your email for enhanced security.'
                response.data['verification_required'] = True
            
            # Set secure cookies
            response.set_cookie(
                key='access_token',
                value=response.data['access'],
                httponly=True,
                samesite='Lax',
                secure=True
            )
            response.set_cookie(
                key='refresh_token',
                value=response.data['refresh'],
                httponly=True,
                samesite='Lax',
                secure=True
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Login failed',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TalentLoginView(BaseLoginView):
    """
    Login endpoint specifically for Talent users
    """
    serializer_class = TalentLoginSerializer

    def post(self, request, *args, **kwargs):
        # The TalentLoginSerializer already validates is_talent flag
        # No need for additional checks here
        return super().post(request, *args, **kwargs)

class BackgroundLoginView(BaseLoginView):
    """
    Login endpoint specifically for Background users
    """
    serializer_class = BackGroundJobsLoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if not response.data.get('is_background'):
            return Response({
                'message': 'This account is not registered as Background'
            }, status=status.HTTP_403_FORBIDDEN)
        return response

class DashboardLoginView(BaseLoginView):
    """
    Unified login endpoint for both regular Dashboard users and Admin Dashboard users
    The view automatically detects the user type based on the request data and permissions
    """
    serializer_class = DashboardLoginSerializer

    def get_serializer_class(self):
        # Check if admin login is requested via query parameter first
        if hasattr(self, 'request') and hasattr(self.request, 'query_params'):
            if self.request.query_params.get('admin_login') == 'true':
                logger.info("Admin login detected via query parameter")
                return AdminDashboardLoginSerializer
        elif hasattr(self, 'request') and hasattr(self.request, 'GET'):
            if self.request.GET.get('admin_login') == 'true':
                logger.info("Admin login detected via request.GET")
                return AdminDashboardLoginSerializer
        
        # For POST requests, we need to check the request body
        import json
        try:
            if hasattr(self, 'request') and hasattr(self.request, 'body') and self.request.body:
                body_data = json.loads(self.request.body)
                if body_data.get('admin_login') == 'true':
                    logger.info("Admin login detected via request body")
                    return AdminDashboardLoginSerializer
        except (json.JSONDecodeError, AttributeError):
            pass
            
        # Check request.data (already parsed by DRF)
        if hasattr(self, 'request') and hasattr(self.request, 'data') and self.request.data:
            if self.request.data.get('admin_login') == 'true':
                logger.info("Admin login detected via request.data")
                return AdminDashboardLoginSerializer
            
        logger.info("Using regular dashboard login serializer")
        return DashboardLoginSerializer

    def post(self, request, *args, **kwargs):
        # Use the correct serializer based on get_serializer_class()
        self.serializer_class = self.get_serializer_class()
        
        # Get the response from the parent class
        response = super().post(request, *args, **kwargs)
        
        # Debug: Log response data
        logger.info(f"Login response data: {response.data}")
        
        # IMPORTANT: The serializer validation should have already added the flags
        # If they're missing, there's a deeper issue
        if 'is_dashboard' not in response.data:
            logger.error("is_dashboard flag missing from response data!")
            logger.error(f"Available keys: {list(response.data.keys())}")
            return Response({
                'message': 'Internal server error: User flags not found'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check if user is a dashboard user
        if not response.data.get('is_dashboard'):
            return Response({
                'message': 'This account is not registered as a Dashboard user'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if admin login was requested and verify admin status
        is_admin_login = False
        try:
            if request.query_params.get('admin_login') == 'true':
                is_admin_login = True
            elif hasattr(request, 'body') and request.body:
                body_data = json.loads(request.body)
                if body_data.get('admin_login') == 'true':
                    is_admin_login = True
        except (json.JSONDecodeError, AttributeError):
            pass
            
        logger.info(f"Admin login requested: {is_admin_login}")
        logger.info(f"is_dashboard_admin in response: {response.data.get('is_dashboard_admin')}")
            
        if is_admin_login and not response.data.get('is_dashboard_admin'):
            return Response({
                'message': 'This account is not registered as an Admin Dashboard user'
            }, status=status.HTTP_403_FORBIDDEN)
            
        return response

class DashboardUserManagementView(APIView):
    """View for admin dashboard users to manage regular dashboard users"""
    permission_classes = [IsAdminDashboardUser]
    
    def get(self, request):
        """List all dashboard users"""
        dashboard_users = BaseUser.objects.filter(is_dashboard=True)
        # Exclude admin users if requested
        if request.query_params.get('exclude_admins') == 'true':
            dashboard_users = dashboard_users.filter(is_staff=False)
            
        user_data = [{
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined,
            'is_active': user.is_active
        } for user in dashboard_users]
        
        return Response(user_data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new dashboard user"""
        # Add is_dashboard=True to the request data
        data = request.data.copy()
        data['role'] = 'dashboard'
        
        serializer = UnifiedUserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Dashboard user created successfully',
                'id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Failed to create dashboard user',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class DashboardUserDetailView(APIView):
    """View for admin dashboard users to manage a specific dashboard user"""
    permission_classes = [IsAdminDashboardUser]
    
    def get_object(self, pk):
        try:
            user = BaseUser.objects.get(pk=pk, is_dashboard=True)
            return user
        except BaseUser.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        """Get details of a specific dashboard user"""
        user = self.get_object(pk)
        data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined,
            'is_active': user.is_active
        }
        return Response(data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        """Delete a dashboard user"""
        user = self.get_object(pk)
        # Prevent admin users from deleting themselves
        if user.id == request.user.id:
            return Response({
                'message': 'You cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        # Prevent deleting other admin users
        if user.is_staff and user.id != request.user.id:
            return Response({
                'message': 'You cannot delete other admin users'
            }, status=status.HTTP_403_FORBIDDEN)
            
        user.delete()
        return Response({
            'message': 'Dashboard user deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class VerifyEmailCodeView(APIView):
    """
    New endpoint to verify email using 6-digit code instead of token
    """
    def post(self, request):
        code = request.data.get('code')
        email = request.data.get('email')
        
        logger.info(f"Email verification attempt with code for: {email}")
        
        if not code or not email:
            logger.warning("Email verification failed: Missing code or email")
            return Response({
                'success': False,
                'message': 'Verification code and email are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find user with the code and email
            user = BaseUser.objects.get(email=email, email_verification_code=code)
            logger.info(f"Found user for code verification: {user.email}")
        except BaseUser.DoesNotExist:
            logger.warning(f"Email verification failed: Invalid code {code} for {email}")
            return Response({
                'success': False,
                'message': 'Invalid verification code'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user is already verified
        if user.email_verified:
            logger.info(f"User {user.email} is already verified")
            return Response({
                'success': True,
                'message': 'Email is already verified'
            }, status=status.HTTP_200_OK)

        # Check if code has expired (24 hours)
        if user.email_verification_code_created:
            code_age = timezone.now() - user.email_verification_code_created
            if code_age > timedelta(hours=24):
                logger.info(f"Code expired for user {user.email}")
                return Response({
                    'success': False,
                    'message': 'Verification code has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Verify the email
        logger.info(f"Verifying email with code for user: {user.email}")
        user.email_verified = True
        user.email_verification_code = None
        user.email_verification_code_created = None
        user.save(update_fields=['email_verified', 'email_verification_code', 'email_verification_code_created'])
        
        logger.info(f"Email successfully verified with code for user: {user.email}")
        return Response({
            'success': True,
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)

class ResendVerificationCodeView(APIView):
    """
    Endpoint to resend verification code to user's email
    """
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'success': False,
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = BaseUser.objects.get(email=email)
        except BaseUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if user is already verified
        if user.email_verified:
            return Response({
                'success': True,
                'message': 'Email is already verified'
            }, status=status.HTTP_200_OK)

        # Generate new verification code
        import random
        verification_code = str(random.randint(100000, 999999))
        user.email_verification_code = verification_code
        user.email_verification_code_created = timezone.now()
        user.last_verification_email_sent = timezone.now()
        user.save()

        # Send verification code email
        from .serializers import send_verification_code_email
        success = send_verification_code_email(user.email, verification_code)

        if success:
            logger.info(f"Resent verification code to {user.email}")
            return Response({
                'success': True,
                'message': 'Verification code sent to your email'
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Failed to resend verification code to {user.email}")
            return Response({
                'success': False,
                'message': 'Failed to send verification code'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    