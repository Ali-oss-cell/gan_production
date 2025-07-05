from django.core.management.base import BaseCommand
from django.db import transaction
from payments.models import PaymentMethodSupport
from payments.payment_methods_config import PAYMENT_METHODS_CONFIG, REGIONAL_PREFERENCES
from decimal import Decimal

class Command(BaseCommand):
    help = 'Set up payment methods with regional support'

    def add_arguments(self, parser):
        parser.add_argument(
            '--region',
            type=str,
            help='Specific region to set up (e.g., us, eu, global)',
        )
        parser.add_argument(
            '--method',
            type=str,
            help='Specific payment method to set up',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing payment method support data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing payment method support data...')
            PaymentMethodSupport.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        if options['region'] and options['method']:
            self.setup_specific_method(options['region'], options['method'])
        elif options['region']:
            self.setup_region(options['region'])
        elif options['method']:
            self.setup_method(options['method'])
        else:
            self.setup_all_methods()

    def setup_all_methods(self):
        """Set up all payment methods for all regions"""
        self.stdout.write('Setting up all payment methods...')
        
        for method, config in PAYMENT_METHODS_CONFIG.items():
            self.setup_method(method)
        
        self.stdout.write(self.style.SUCCESS('Successfully set up all payment methods'))

    def setup_method(self, method):
        """Set up a specific payment method for all supported regions"""
        config = PAYMENT_METHODS_CONFIG.get(method)
        if not config:
            self.stdout.write(self.style.ERROR(f'Unknown payment method: {method}'))
            return

        self.stdout.write(f'Setting up {method}...')

        if config.get('global_support', False):
            # Set up for global support
            self.create_payment_method_support(method, 'global', 'USD', config)
        else:
            # Set up for specific regions
            supported_regions = config.get('supported_regions', [])
            for region in supported_regions:
                self.create_payment_method_support(method, region, 'USD', config)

        self.stdout.write(self.style.SUCCESS(f'Successfully set up {method}'))

    def setup_region(self, region):
        """Set up all payment methods for a specific region"""
        self.stdout.write(f'Setting up payment methods for region: {region}')

        for method, config in PAYMENT_METHODS_CONFIG.items():
            if config.get('global_support', False) or region in config.get('supported_regions', []):
                self.create_payment_method_support(method, region, 'USD', config)

        self.stdout.write(self.style.SUCCESS(f'Successfully set up payment methods for {region}'))

    def setup_specific_method(self, region, method):
        """Set up a specific payment method for a specific region"""
        config = PAYMENT_METHODS_CONFIG.get(method)
        if not config:
            self.stdout.write(self.style.ERROR(f'Unknown payment method: {method}'))
            return

        if not config.get('global_support', False) and region not in config.get('supported_regions', []):
            self.stdout.write(self.style.ERROR(f'Payment method {method} not supported in region {region}'))
            return

        self.stdout.write(f'Setting up {method} for region {region}...')
        self.create_payment_method_support(method, region, 'USD', config)
        self.stdout.write(self.style.SUCCESS(f'Successfully set up {method} for {region}'))

    def create_payment_method_support(self, method, region, currency, config):
        """Create a PaymentMethodSupport record"""
        try:
            with transaction.atomic():
                payment_support, created = PaymentMethodSupport.objects.get_or_create(
                    payment_method=method,
                    region=region,
                    currency=currency,
                    defaults={
                        'is_active': True,
                        'min_amount': config.get('min_amount'),
                        'max_amount': config.get('max_amount'),
                        'processing_fee': config.get('processing_fee', Decimal('0')),
                        'fixed_fee': config.get('fixed_fee', Decimal('0')),
                        'stripe_payment_method_type': config.get('stripe_type'),
                        'notes': config.get('description', ''),
                    }
                )

                if created:
                    self.stdout.write(f'  Created: {method} for {region}')
                else:
                    self.stdout.write(f'  Updated: {method} for {region}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up {method} for {region}: {str(e)}'))

    def display_current_setup(self):
        """Display current payment method setup"""
        self.stdout.write('\nCurrent Payment Method Setup:')
        self.stdout.write('=' * 50)
        
        for region in REGIONAL_PREFERENCES.keys():
            methods = PaymentMethodSupport.objects.filter(region=region, is_active=True)
            if methods.exists():
                self.stdout.write(f'\n{region.upper()}:')
                for method in methods:
                    self.stdout.write(f'  - {method.payment_method} ({method.currency})')
                    self.stdout.write(f'    Min: {method.min_amount}, Max: {method.max_amount}')
                    self.stdout.write(f'    Fee: {method.processing_fee}% + ${method.fixed_fee}') 