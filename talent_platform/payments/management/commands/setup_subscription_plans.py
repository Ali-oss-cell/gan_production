from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan
from payments.pricing_config import SUBSCRIPTION_PLANS
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Sets up the subscription plans for the platform'

    def handle(self, *args, **options):
        # Create or update plans from pricing_config
        for plan_key, plan_data in SUBSCRIPTION_PLANS.items():
            # Convert plan key to lowercase for database name
            plan_name = plan_key.lower()
            if plan_key == 'BACKGROUND_JOBS':
                plan_name = 'background_jobs'
            
            # Get the actual Stripe price ID from settings
            stripe_price_id = plan_data['stripe_price_id']
            if not stripe_price_id:
                # Fallback to environment variables if pricing_config returns None
                price_id_mapping = {
                    'premium': os.getenv('STRIPE_PREMIUM_PRICE_ID'),
                    'platinum': os.getenv('STRIPE_PLATINUM_PRICE_ID'),
                    'bands': os.getenv('STRIPE_BANDS_PRICE_ID'),
                    'background_jobs': os.getenv('STRIPE_BACKGROUND_JOBS_PRICE_ID'),
                }
                stripe_price_id = price_id_mapping.get(plan_name, f'price_{plan_name}')
                
            self.stdout.write(f'Processing {plan_name} with Stripe ID: {stripe_price_id}')
                
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_name,
                defaults={
                    'description': f"{plan_data['name']} Plan - {', '.join(plan_data['features'][:3])}...",
                    'price': plan_data['price'],
                    'stripe_price_id': stripe_price_id,
                    'features': plan_data['features'],
                    'duration_months': plan_data['duration_months'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {plan.name} plan'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated {plan.name} plan')) 