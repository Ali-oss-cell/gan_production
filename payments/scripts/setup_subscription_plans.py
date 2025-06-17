from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan

class Command(BaseCommand):
    help = 'Sets up the subscription plans for the platform'

    def handle(self, *args, **options):
        # Define subscription plans
        plans = [
            {
                'name': 'silver',
                'description': 'Silver Plan - Basic features for talent users',
                'price': 9.99,
                'stripe_price_id': 'price_silver',  # Replace with actual Stripe price ID
                'features': {
                    'profile_visibility': 'basic',
                    'job_applications': 10,
                    'skill_verification': False,
                    'priority_support': False
                }
            },
            {
                'name': 'gold',
                'description': 'Gold Plan - Enhanced features for talent users',
                'price': 19.99,
                'stripe_price_id': 'price_gold',  # Replace with actual Stripe price ID
                'features': {
                    'profile_visibility': 'enhanced',
                    'job_applications': 25,
                    'skill_verification': True,
                    'priority_support': True
                }
            },
            {
                'name': 'platinum',
                'description': 'Platinum Plan - Premium features for talent users',
                'price': 29.99,
                'stripe_price_id': 'price_platinum',  # Replace with actual Stripe price ID
                'features': {
                    'profile_visibility': 'premium',
                    'job_applications': 'unlimited',
                    'skill_verification': True,
                    'priority_support': True,
                    'featured_profile': True
                }
            },
            {
                'name': 'back_ground_jobs',
                'description': 'Background Jobs Plan - For background job users',
                'price': 49.99,
                'stripe_price_id': 'price_background',  # Replace with actual Stripe price ID
                'features': {
                    'job_postings': 'unlimited',
                    'applicant_tracking': True,
                    'analytics': True,
                    'priority_support': True
                }
            }
        ]

        # Create or update plans
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults={
                    'description': plan_data['description'],
                    'price': plan_data['price'],
                    'stripe_price_id': plan_data['stripe_price_id'],
                    'features': plan_data['features'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {plan.name} plan'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated {plan.name} plan')) 