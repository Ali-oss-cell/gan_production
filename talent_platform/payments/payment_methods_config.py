from decimal import Decimal
from django.conf import settings

# Payment Method Configuration
PAYMENT_METHODS_CONFIG = {
    'card': {
        'name': 'Credit/Debit Card',
        'stripe_type': 'card',
        'global_support': True,
        'processing_fee': Decimal('2.9'),
        'fixed_fee': Decimal('0.30'),
        'min_amount': Decimal('0.50'),
        'max_amount': Decimal('999999.99'),
        'description': 'Visa, Mastercard, American Express, Discover',
    },
    'apple_pay': {
        'name': 'Apple Pay',
        'stripe_type': 'card',
        'global_support': False,
        'supported_regions': ['us', 'ca', 'au', 'uk', 'eu', 'sg', 'jp', 'kr', 'ae'],
        'processing_fee': Decimal('2.9'),
        'fixed_fee': Decimal('0.30'),
        'min_amount': Decimal('0.50'),
        'max_amount': Decimal('999999.99'),
        'description': 'Apple Pay for iOS devices',
    },
    'google_pay': {
        'name': 'Google Pay',
        'stripe_type': 'card',
        'global_support': False,
        'supported_regions': ['us', 'ca', 'au', 'uk', 'eu', 'sg', 'jp', 'kr', 'in', 'br', 'mx', 'ae'],
        'processing_fee': Decimal('2.9'),
        'fixed_fee': Decimal('0.30'),
        'min_amount': Decimal('0.50'),
        'max_amount': Decimal('999999.99'),
        'description': 'Google Pay for Android devices',
    },
    'paypal': {
        'name': 'PayPal',
        'stripe_type': 'paypal',
        'global_support': True,
        'processing_fee': Decimal('3.5'),
        'fixed_fee': Decimal('0.35'),
        'min_amount': Decimal('1.00'),
        'max_amount': Decimal('10000.00'),
        'description': 'PayPal account or guest checkout',
    },
    'bank_transfer': {
        'name': 'Bank Transfer',
        'stripe_type': 'us_bank_account',
        'global_support': False,
        'supported_regions': ['us'],
        'processing_fee': Decimal('0.8'),
        'fixed_fee': Decimal('0.00'),
        'min_amount': Decimal('1.00'),
        'max_amount': Decimal('25000.00'),
        'description': 'Direct bank transfer (ACH)',
    },
    'sepa_debit': {
        'name': 'SEPA Direct Debit',
        'stripe_type': 'sepa_debit',
        'global_support': False,
        'supported_regions': ['eu'],
        'processing_fee': Decimal('0.8'),
        'fixed_fee': Decimal('0.00'),
        'min_amount': Decimal('1.00'),
        'max_amount': Decimal('15000.00'),
        'description': 'SEPA Direct Debit for EU',
    },
    'alipay': {
        'name': 'Alipay',
        'stripe_type': 'alipay',
        'global_support': False,
        'supported_regions': ['cn'],
        'processing_fee': Decimal('2.9'),
        'fixed_fee': Decimal('0.30'),
        'min_amount': Decimal('0.01'),
        'max_amount': Decimal('50000.00'),
        'description': 'Alipay for China',
    },
    'wechat_pay': {
        'name': 'WeChat Pay',
        'stripe_type': 'wechat_pay',
        'global_support': False,
        'supported_regions': ['cn'],
        'processing_fee': Decimal('2.9'),
        'fixed_fee': Decimal('0.30'),
        'min_amount': Decimal('0.01'),
        'max_amount': Decimal('50000.00'),
        'description': 'WeChat Pay for China',
    },
    'afterpay': {
        'name': 'Afterpay',
        'stripe_type': 'afterpay_clearpay',
        'global_support': False,
        'supported_regions': ['us', 'ca', 'au', 'uk'],
        'processing_fee': Decimal('4.0'),
        'fixed_fee': Decimal('0.30'),
        'min_amount': Decimal('35.00'),
        'max_amount': Decimal('2000.00'),
        'description': 'Buy now, pay later in 4 installments',
    },
    'klarna': {
        'name': 'Klarna',
        'stripe_type': 'klarna',
        'global_support': False,
        'supported_regions': ['us', 'eu', 'uk', 'au'],
        'processing_fee': Decimal('3.5'),
        'fixed_fee': Decimal('0.30'),
        'min_amount': Decimal('10.00'),
        'max_amount': Decimal('10000.00'),
        'description': 'Pay later or in installments',
    },
    'mada': {
        'name': 'Mada',
        'stripe_type': 'card',
        'global_support': False,
        'supported_regions': ['sa', 'ae'],
        'processing_fee': Decimal('2.9'),
        'fixed_fee': Decimal('0.30'),
        'min_amount': Decimal('0.50'),
        'max_amount': Decimal('999999.99'),
        'description': 'Mada cards for Saudi Arabia',
    },
    'unionpay': {
        'name': 'UnionPay',
        'stripe_type': 'card',
        'global_support': False,
        'supported_regions': ['cn', 'ae', 'sg', 'my', 'th', 'vn', 'id'],
        'processing_fee': Decimal('2.9'),
        'fixed_fee': Decimal('0.30'),
        'min_amount': Decimal('0.50'),
        'max_amount': Decimal('999999.99'),
        'description': 'UnionPay cards for China and Asia',
    },
}

# Regional Payment Method Preferences
REGIONAL_PREFERENCES = {
    'us': ['card', 'apple_pay', 'google_pay', 'paypal', 'afterpay', 'klarna', 'bank_transfer'],
    'eu': ['card', 'apple_pay', 'google_pay', 'paypal', 'sepa_debit', 'klarna'],
    'uk': ['card', 'apple_pay', 'google_pay', 'paypal', 'klarna', 'afterpay'],
    'ca': ['card', 'apple_pay', 'google_pay', 'paypal', 'afterpay'],
    'au': ['card', 'apple_pay', 'google_pay', 'paypal', 'afterpay', 'klarna'],
    'cn': ['card', 'alipay', 'wechat_pay'],
    'ae': ['card', 'apple_pay', 'google_pay', 'paypal', 'mada', 'unionpay'],  # UAE
    'sa': ['card', 'apple_pay', 'google_pay', 'paypal', 'mada'],  # Saudi Arabia
    'global': ['card', 'paypal'],
}

def get_supported_payment_methods(region, currency='USD', amount=None):
    """Get supported payment methods for a region and currency"""
    from .models import PaymentMethodSupport
    
    return PaymentMethodSupport.get_available_methods(region, currency, amount)

def get_payment_method_config(method):
    """Get configuration for a specific payment method"""
    return PAYMENT_METHODS_CONFIG.get(method, {})

def get_regional_preferences(region):
    """Get preferred payment methods for a region"""
    return REGIONAL_PREFERENCES.get(region, ['card', 'paypal'])

def is_payment_method_supported(method, region):
    """Check if a payment method is supported in a region"""
    config = get_payment_method_config(method)
    if not config:
        return False
    
    if config.get('global_support', False):
        return True
    
    supported_regions = config.get('supported_regions', [])
    return region in supported_regions 