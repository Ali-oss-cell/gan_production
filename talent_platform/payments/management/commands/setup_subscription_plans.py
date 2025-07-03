from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan
from payments.pricing_config import SUBSCRIPTION_PLANS

class Command(BaseCommand):
    help = 'Sets up the subscription plans for the platform'

    def handle(self, *args, **options):
        # Create or update plans from pricing_config
        for plan_key, plan_data in SUBSCRIPTION_PLANS.items():
            # Convert plan key to lowercase for database name
            plan_name = plan_key.lower()
            if plan_key == 'BACKGROUND_JOBS':
                plan_name = 'background_jobs'
                
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_name,
                defaults={
                    'description': f"{plan_data['name']} Plan - {', '.join(plan_data['features'][:3])}...",
                    'price': plan_data['price'],
                    'stripe_price_id': plan_data['stripe_price_id'],
                    'features': plan_data['features'],
                    'duration_months': plan_data['duration_months'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {plan.name} plan'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated {plan.name} plan')) 