from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet,
    SubscriptionViewSet,
    PaymentTransactionViewSet,
    stripe_webhook,
    PricingView,
    CreateCheckoutSessionView
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='plan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'transactions', PaymentTransactionViewSet, basename='transaction')

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Stripe webhook endpoint
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    
    # Pricing information endpoint
    path('pricing/', PricingView.as_view(), name='pricing'),
    
    # Checkout session creation endpoint
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    
    # Additional endpoints
    path('plans/pricing/', SubscriptionPlanViewSet.as_view({'get': 'pricing'}), name='plans-pricing'),

]