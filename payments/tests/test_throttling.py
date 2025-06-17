from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIClient
from rest_framework import status

from payments.middleware import UserTypeThrottlingMiddleware
from payments.throttling import (
    AnonymousRateThrottle,
    TalentUserRateThrottle,
    BackgroundUserRateThrottle,
    DashboardUserRateThrottle,
    AdminDashboardUserRateThrottle,
    PaymentEndpointRateThrottle,
    RestrictedCountryRateThrottle
)

User = get_user_model()


class ThrottlingMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = UserTypeThrottlingMiddleware(get_response=lambda request: None)
        
        # Create different types of users
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User'
        )
        
        self.dashboard_admin = User.objects.create_user(
            email='dashboard_admin@example.com',
            password='password123',
            first_name='Dashboard',
            last_name='Admin',
            is_dashboard_admin=True
        )
        
        self.dashboard_user = User.objects.create_user(
            email='dashboard@example.com',
            password='password123',
            first_name='Dashboard',
            last_name='User',
            is_dashboard=True
        )
        
        self.talent_user = User.objects.create_user(
            email='talent@example.com',
            password='password123',
            first_name='Talent',
            last_name='User',
            is_talent=True
        )
        
        self.background_user = User.objects.create_user(
            email='background@example.com',
            password='password123',
            first_name='Background',
            last_name='User',
            is_background=True
        )
        
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='password123',
            first_name='Regular',
            last_name='User'
        )
    
    def test_anonymous_user_throttle_scope(self):
        request = self.factory.get('/api/some-endpoint/')
        request.user = AnonymousUser()
        
        self.middleware.process_request(request)
        self.assertEqual(request.throttle_scope, 'anon')
    
    def test_superuser_throttle_scope(self):
        request = self.factory.get('/api/some-endpoint/')
        request.user = self.admin_user
        
        self.middleware.process_request(request)
        self.assertEqual(request.throttle_scope, 'admin_dashboard_user')
    
    def test_dashboard_admin_throttle_scope(self):
        request = self.factory.get('/api/some-endpoint/')
        request.user = self.dashboard_admin
        
        self.middleware.process_request(request)
        self.assertEqual(request.throttle_scope, 'admin_dashboard_user')
    
    def test_dashboard_user_throttle_scope(self):
        request = self.factory.get('/api/some-endpoint/')
        request.user = self.dashboard_user
        
        self.middleware.process_request(request)
        self.assertEqual(request.throttle_scope, 'dashboard_user')
    
    def test_talent_user_throttle_scope(self):
        request = self.factory.get('/api/some-endpoint/')
        request.user = self.talent_user
        
        self.middleware.process_request(request)
        self.assertEqual(request.throttle_scope, 'talent_user')
    
    def test_background_user_throttle_scope(self):
        request = self.factory.get('/api/some-endpoint/')
        request.user = self.background_user
        
        self.middleware.process_request(request)
        self.assertEqual(request.throttle_scope, 'background_user')
    
    def test_regular_user_throttle_scope(self):
        request = self.factory.get('/api/some-endpoint/')
        request.user = self.regular_user
        
        self.middleware.process_request(request)
        self.assertEqual(request.throttle_scope, 'user')


class ThrottlingAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            is_talent=True
        )
    
    def test_api_throttling_headers(self):
        """Test that throttling headers are included in API responses"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/payments/pricing/')
        
        # Check that the response includes throttling headers
        self.assertIn('X-RateLimit-Limit', response.headers)
        self.assertIn('X-RateLimit-Remaining', response.headers)
        self.assertIn('X-RateLimit-Reset', response.headers)
    
    def test_payment_endpoint_throttling(self):
        """Test that payment endpoints use the payment_endpoints throttle scope"""
        self.client.force_authenticate(user=self.user)
        
        # Make multiple requests to trigger throttling
        for _ in range(31):  # payment_endpoints is set to 30/hour
            self.client.get('/api/payments/pricing/')
        
        # The 31st request should be throttled
        response = self.client.get('/api/payments/pricing/')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)