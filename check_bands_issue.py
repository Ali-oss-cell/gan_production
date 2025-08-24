import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from payments.models import SubscriptionPlan, Subscription
from django.contrib.auth import get_user_model

User = get_user_model()

print('=== Available Subscription Plans ===')
for plan in SubscriptionPlan.objects.all():
    print(f'ID: {plan.id}, Name: "{plan.name}", Stripe Price ID: {plan.stripe_price_id}')

print('\n=== Current Subscriptions ===')
for sub in Subscription.objects.all():
    print(f'User: {sub.user.email}, Plan: "{sub.plan.name}", Status: {sub.status}, Active: {sub.is_active}')

print('\n=== Checking for bands subscriptions specifically ===')
bands_subs = Subscription.objects.filter(plan__name='bands', is_active=True, status='active')
print(f'Found {bands_subs.count()} active bands subscriptions with name="bands"')

bands_subs_capital = Subscription.objects.filter(plan__name='Bands', is_active=True, status='active')
print(f'Found {bands_subs_capital.count()} active bands subscriptions with name="Bands"')

print('\n=== Testing band API logic ===')
# Test the exact logic used in band_views.py
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    user = User.objects.get(email='wewe@wewe.com')
    print(f'Testing for user: {user.email}')
    
    # This is the exact query from band_views.py line 50-55
    has_bands_subscription = Subscription.objects.filter(
        user=user,
        plan__name='bands',  # lowercase 'bands'
        is_active=True,
        status='active'
    ).exists()
    print(f'has_bands_subscription (lowercase): {has_bands_subscription}')
    
    # Test with capital 'Bands'
    has_bands_subscription_capital = Subscription.objects.filter(
        user=user,
        plan__name='Bands',  # capital 'Bands'
        is_active=True,
        status='active'
    ).exists()
    print(f'has_bands_subscription (capital): {has_bands_subscription_capital}')
    
except User.DoesNotExist:
    print('User wewe@wewe.com not found')
