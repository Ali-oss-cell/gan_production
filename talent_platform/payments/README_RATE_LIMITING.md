# Rate Limiting Implementation

## Overview

This document explains the rate limiting (throttling) implementation in the Talent Platform API. Rate limiting helps protect the API from abuse and ensures fair usage across all users.

## Configuration

Rate limiting is implemented using Django REST Framework's throttling classes. The configuration is defined in `settings.py` under the `REST_FRAMEWORK` dictionary.

### Default Throttle Rates

```python
'DEFAULT_THROTTLE_RATES': {
    'anon': '30/hour',           # Anonymous users
    'user': '100/hour',          # Authenticated users (default)
    'talent_user': '100/hour',   # Talent users
    'background_user': '100/hour', # Background users
    'dashboard_user': '200/hour', # Dashboard users
    'admin_dashboard_user': '300/hour', # Admin dashboard users
    'payment_endpoints': '30/hour', # Payment processing endpoints
    'restricted_country': '50/hour', # Restricted country management
}
```

## Custom Throttling Classes

Custom throttling classes are defined in `payments/throttling.py`:

- `AnonymousRateThrottle`: For unauthenticated users
- `TalentUserRateThrottle`: For talent users
- `BackgroundUserRateThrottle`: For background users
- `DashboardUserRateThrottle`: For dashboard users
- `AdminDashboardUserRateThrottle`: For admin dashboard users
- `PaymentEndpointRateThrottle`: For payment processing endpoints
- `RestrictedCountryRateThrottle`: For restricted country management

## User-Type Based Throttling

The `UserTypeThrottlingMiddleware` automatically applies the appropriate throttle scope based on the user type. This middleware is registered in `settings.py` and sets the `request.throttle_scope` attribute based on the authenticated user's type.

## View-Specific Throttling

Some views have specific throttling requirements and explicitly set the `throttle_scope` attribute:

- `RestrictedCountryUserViewSet`: Uses 'restricted_country' scope
- `SubscriptionViewSet`: Uses 'payment_endpoints' scope
- `PaymentTransactionViewSet`: Uses 'payment_endpoints' scope
- `PricingView`: Uses 'payment_endpoints' scope

## Response Headers

When rate limiting is applied, the API includes the following headers in responses:

- `X-RateLimit-Limit`: The maximum number of requests allowed in the current period
- `X-RateLimit-Remaining`: The number of requests remaining in the current period
- `X-RateLimit-Reset`: The time when the current rate limit window resets

## Handling Rate Limit Exceeded

When a client exceeds the rate limit, the API returns a 429 Too Many Requests response with a message indicating when they can retry.

## Recommendations for Clients

Clients should:

1. Cache responses when appropriate to reduce API calls
2. Implement exponential backoff when receiving 429 responses
3. Monitor rate limit headers to avoid hitting limits
4. Distribute requests evenly rather than sending bursts