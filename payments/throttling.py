from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class AnonymousRateThrottle(AnonRateThrottle):
    """
    Throttle for anonymous users with stricter limits.
    """
    scope = 'anon'

class TalentUserRateThrottle(UserRateThrottle):
    """
    Throttle for authenticated talent users.
    """
    scope = 'talent_user'

class BackgroundUserRateThrottle(UserRateThrottle):
    """
    Throttle for authenticated background users.
    """
    scope = 'background_user'

class DashboardUserRateThrottle(UserRateThrottle):
    """
    Throttle for authenticated dashboard users.
    """
    scope = 'dashboard_user'

class AdminDashboardUserRateThrottle(UserRateThrottle):
    """
    Throttle for authenticated admin dashboard users with higher limits.
    """
    scope = 'admin_dashboard_user'

class PaymentEndpointRateThrottle(UserRateThrottle):
    """
    Stricter throttle for payment processing endpoints to prevent abuse.
    """
    scope = 'payment_endpoints'

class RestrictedCountryRateThrottle(UserRateThrottle):
    """
    Throttle for restricted country user management endpoints.
    """
    scope = 'restricted_country'