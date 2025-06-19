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
    rate = '100/hour'

class BackgroundUserRateThrottle(UserRateThrottle):
    """
    Throttle for authenticated background users.
    """
    scope = 'background_user'
    rate = '100/hour'

class DashboardUserRateThrottle(UserRateThrottle):
    """
    Throttle for authenticated dashboard users.
    """
    scope = 'dashboard_user'
    rate = '500/hour'

class AdminDashboardUserRateThrottle(UserRateThrottle):
    """
    Throttle for authenticated admin dashboard users with higher limits.
    """
    scope = 'admin_dashboard_user'
    rate = '2000/hour'

class PaymentEndpointRateThrottle(UserRateThrottle):
    """
    Stricter throttle for payment processing endpoints to prevent abuse.
    """
    scope = 'payment_endpoints'
    rate = '30/hour'

class RestrictedCountryRateThrottle(UserRateThrottle):
    """
    Throttle for restricted country user management endpoints.
    """
    scope = 'restricted_country'
    rate = '50/hour'