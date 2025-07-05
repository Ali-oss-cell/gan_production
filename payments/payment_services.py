import stripe
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import PaymentTransaction, PaymentMethodSupport
from .payment_methods_config import get_payment_method_config, is_payment_method_supported

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentMethodService:
    """Service for handling payment methods"""
    
    @staticmethod
    def get_available_methods(user, amount=None, currency='USD'):
        """Get available payment methods for a user based on their region"""
        # Get user's region (you might need to implement this based on your user model)
        region = getattr(user, 'country', 'us').lower()
        
        # Get supported methods from database
        available_methods = PaymentMethodSupport.get_available_methods(
            region, currency, amount
        )
        
        # Filter by amount limits
        if amount:
            filtered_methods = []
            for method in available_methods:
                config = get_payment_method_config(method)
                if config:
                    min_amount = config.get('min_amount', Decimal('0'))
                    max_amount = config.get('max_amount', Decimal('999999.99'))
                    if min_amount <= amount <= max_amount:
                        filtered_methods.append(method)
            return filtered_methods
        
        return list(available_methods)
    
    @staticmethod
    def create_payment_intent(user, amount, currency='USD', payment_method='card', metadata=None):
        """Create a Stripe payment intent"""
        try:
            # Get payment method configuration
            config = get_payment_method_config(payment_method)
            if not config:
                raise ValueError(f"Unsupported payment method: {payment_method}")
            
            # Check if payment method is supported in user's region
            region = getattr(user, 'country', 'us').lower()
            if not is_payment_method_supported(payment_method, region):
                raise ValueError(f"Payment method {payment_method} not supported in {region}")
            
            # Calculate fees
            processing_fee = config.get('processing_fee', Decimal('0'))
            fixed_fee = config.get('fixed_fee', Decimal('0'))
            total_fee = (amount * processing_fee / 100) + fixed_fee
            total_amount = amount + total_fee
            
            # Create payment intent
            intent_data = {
                'amount': int(total_amount * 100),  # Convert to cents
                'currency': currency.lower(),
                'payment_method_types': [config['stripe_type']],
                'metadata': {
                    'user_id': str(user.id),
                    'payment_method': payment_method,
                    'processing_fee': str(total_fee),
                    **(metadata or {})
                }
            }
            
            # Add specific payment method data
            if payment_method in ['apple_pay', 'google_pay']:
                intent_data['payment_method_options'] = {
                    'card': {
                        'request_three_d_secure': 'automatic'
                    }
                }
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': total_amount,
                'processing_fee': total_fee,
                'currency': currency
            }
            
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Payment intent creation failed: {str(e)}")
    
    @staticmethod
    def confirm_payment(payment_intent_id, payment_method_id=None):
        """Confirm a payment intent"""
        try:
            if payment_method_id:
                stripe.PaymentIntent.confirm(
                    payment_intent_id,
                    payment_method=payment_method_id
                )
            else:
                stripe.PaymentIntent.confirm(payment_intent_id)
            
            return True
        except stripe.error.StripeError as e:
            raise ValueError(f"Payment confirmation failed: {str(e)}")
    
    @staticmethod
    def create_payment_transaction(user, payment_intent_id, amount, payment_method, subscription=None):
        """Create a payment transaction record"""
        try:
            # Get payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Create transaction record
            transaction = PaymentTransaction.objects.create(
                user=user,
                subscription=subscription,
                amount=amount,
                currency=payment_intent.currency.upper(),
                stripe_payment_intent_id=payment_intent_id,
                stripe_charge_id=payment_intent.latest_charge,
                status=payment_intent.status,
                payment_method=payment_method,
                payment_method_details=payment_intent.payment_method_data if hasattr(payment_intent, 'payment_method_data') else None,
                billing_details=payment_intent.charges.data[0].billing_details if payment_intent.charges.data else None
            )
            
            return transaction
            
        except Exception as e:
            raise ValueError(f"Transaction creation failed: {str(e)}")
    
    @staticmethod
    def get_payment_method_details(payment_method_id):
        """Get details of a payment method"""
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            return payment_method
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to retrieve payment method: {str(e)}")
    
    @staticmethod
    def attach_payment_method_to_customer(payment_method_id, customer_id):
        """Attach a payment method to a customer"""
        try:
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            return True
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to attach payment method: {str(e)}")
    
    @staticmethod
    def detach_payment_method(payment_method_id):
        """Detach a payment method from a customer"""
        try:
            stripe.PaymentMethod.detach(payment_method_id)
            return True
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to detach payment method: {str(e)}")

class ApplePayService:
    """Service for Apple Pay specific functionality"""
    
    @staticmethod
    def create_domain_verification_file():
        """Create Apple Pay domain verification file"""
        # This should create a file at .well-known/apple-developer-merchantid-domain-association
        # You'll need to get the actual content from Apple
        verification_content = """
        # Apple Pay Domain Verification File
        # This file should be placed at: .well-known/apple-developer-merchantid-domain-association
        # Get the actual content from Apple Developer Portal
        """
        return verification_content
    
    @staticmethod
    def validate_apple_pay_session(domain, validation_url):
        """Validate Apple Pay session"""
        try:
            # This is a simplified version - you'll need to implement the actual validation
            # according to Apple's documentation
            return True
        except Exception as e:
            raise ValueError(f"Apple Pay validation failed: {str(e)}")

class GooglePayService:
    """Service for Google Pay specific functionality"""
    
    @staticmethod
    def get_google_pay_configuration():
        """Get Google Pay configuration for frontend"""
        return {
            'environment': 'TEST' if settings.DEBUG else 'PRODUCTION',
            'merchantInfo': {
                'merchantName': settings.STRIPE_MERCHANT_NAME,
                'merchantId': settings.STRIPE_MERCHANT_ID,
            },
            'allowedPaymentMethods': [{
                'type': 'CARD',
                'parameters': {
                    'allowedAuthMethods': ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
                    'allowedCardNetworks': ['VISA', 'MASTERCARD', 'AMEX'],
                },
                'tokenizationSpecification': {
                    'type': 'PAYMENT_GATEWAY',
                    'parameters': {
                        'gateway': 'stripe',
                        'gatewayMerchantId': settings.STRIPE_MERCHANT_ID,
                    },
                },
            }],
            'transactionInfo': {
                'totalPriceStatus': 'FINAL',
                'totalPriceLabel': 'Total',
                'currencyCode': 'USD',
                'countryCode': 'US',
            },
        } 