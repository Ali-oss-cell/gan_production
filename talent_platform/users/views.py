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

logger = logging.getLogger(__name__)

class UserRegistrationView(APIView):
    """
    Unified registration endpoint for all user types with improved error handling
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
            
            # Create user
            user = serializer.save()
            
            # Prepare success response
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
            
            # Include email verification status in response
            response.data['email_verified'] = user.email_verified
            if not user.email_verified:
                response.data['message'] = 'Your email is not verified. You can still use your account, but we recommend verifying your email for enhanced security.'
                response.data['verification_url'] = f"http://localhost:3000/verify-email?token={user.email_verification_token}"
            
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
        response = super().post(request, *args, **kwargs)
        if not response.data.get('is_talent'):
            return Response({
                'message': 'This account is not registered as Talent'
            }, status=status.HTTP_403_FORBIDDEN)
        return response

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
        if hasattr(self, 'request') and self.request.query_params.get('admin_login') == 'true':
            logger.info("Admin login detected via query parameter")
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
            
        logger.info("Using regular dashboard login serializer")
        return DashboardLoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Debug: Log response data
        logger.info(f"Login response data: {response.data}")
        
        # Check if user is a dashboard user
        if not response.data.get('is_dashboard'):
            return Response({
                'message': 'This account is not registered as a Dashboard user'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if admin login was requested and verify staff status
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

class VerifyEmailView(APIView):
    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({
                'message': 'Verification token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(BaseUser, email_verification_token=token)

        # Check if token has expired (24 hours)
        if user.email_verification_token_created < timezone.now() - timedelta(hours=24):
            # Generate new token and send new verification email
            import secrets
            user.email_verification_token = secrets.token_urlsafe(32)
            user.email_verification_token_created = timezone.now()
            user.save()

            from django.core.mail import send_mail
            from django.conf import settings
            verification_url = f"http://localhost:3000/verify-email?token={user.email_verification_token}"
            send_mail(
                'New email verification link',
                f'Your previous verification link has expired. Please use this new link to verify your email address: {verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({
                'message': 'Verification link has expired. A new link has been sent to your email.'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_token_created = None
        user.save()

        return Response({
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)