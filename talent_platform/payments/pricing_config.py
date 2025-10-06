from decimal import Decimal
from django.conf import settings

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    'FREE': {
        'name': 'Free',
        'price': Decimal('0.00'),  # Free plan
        'features': [
            '1 profile picture',
            '0 showcase videos',
            'Basic search visibility',
            'Basic profile features',
            'Social media links',
            'Profile verification available',
        ],
        'stripe_price_id': 'price_free',
        'duration_months': 12,
    },
    'PREMIUM': {
        'name': 'Premium',
        'price': Decimal('19.99'),  # Yearly price in USD
        'features': [
            '4 profile pictures',
            '2 showcase videos',
            'Advanced search filters',
            'Priority support',
            'Enhanced search visibility (50% boost)',
            'Social media integration',
            'Basic analytics',
        ],
        'stripe_price_id': 'price_premium',
        'duration_months': 12,
    },
    'PLATINUM': {
        'name': 'Platinum', 
        'price': Decimal('39.99'),  # Yearly price in USD
        'features': [
            '6 profile pictures',
            '4 showcase videos',
            'All search filters',
            'Priority support',
            'Highest search visibility (100% boost)',
            'Custom profile URL',
            'Featured profile placement',
            'Advanced analytics dashboard',
            'Social media integration',
        ],
        'stripe_price_id': 'price_platinum',
        'duration_months': 12,
    },
    'BANDS': {
        'name': 'Bands',
        'price': Decimal('29.99'),  # Yearly price in USD
        'features': [
            'Create and manage bands',
            'Unlimited band members',
            'Band profile with description',
            'Band contact information',
            'Band location and website',
            'Band media uploads (5 images, 5 videos)',
            'Member role management (admin/member)',
            'Member position assignments',
            'Band invitations system',
            'Band analytics and scoring',
            'Band profile pictures',
            'Social media integration for bands',
        ],
        'stripe_price_id': 'price_bands',
        'duration_months': 12,
    },
}

# Additional Pricing Options
ADDITIONAL_SERVICES = {
    'PROFILE_VERIFICATION': {
        'name': 'Profile Verification',
        'price': Decimal('19.99'),
        'description': 'Get your profile verified by our team',
        'stripe_price_id': 'test_price_verification',
    },
    'FEATURED_PLACEMENT': {
        'name': 'Featured Placement',
        'price': Decimal('49.99'),
        'description': 'Get your profile featured for 7 days',
        'stripe_price_id': 'test_price_featured',
    },
    'CUSTOM_URL': {
        'name': 'Custom Profile URL',
        'price': Decimal('9.99'),
        'description': 'Get a custom URL for your profile',
        'stripe_price_id': 'test_price_custom_url',
    },
    'BANDS': {
        'name': 'Bands Package',
        'price': Decimal('350.00'),
        'description': 'Special package for bands and musical groups',
        'stripe_price_id': 'price_1RfJmOP623EsFG0o16QVjMut',  # Bands plan price ID
    },
}

# Discounts and Promotions
PROMOTIONS = {
    'ANNUAL_DISCOUNT': {
        'name': 'Annual Subscription Discount',
        'discount_percentage': 20,  # 20% discount for annual subscription
        'description': 'Save 20% by subscribing annually',
    },
    'NEW_USER_DISCOUNT': {
        'name': 'New User Discount',
        'discount_percentage': 15,  # 15% discount for new users
        'description': '15% off your first year',
        'duration_days': 365,
    },
}

# Currency Configuration
CURRENCY = 'USD'
CURRENCY_SYMBOL = '$'

# Payment Settings
PAYMENT_SETTINGS = {
    'CURRENCY': CURRENCY,
    'CURRENCY_SYMBOL': CURRENCY_SYMBOL,
    'MINIMUM_PAYMENT': Decimal('1.00'),
    'MAXIMUM_PAYMENT': Decimal('9999.99'),
    'REFUND_POLICY_DAYS': 14,  # Number of days for refund policy
}

# Tax Configuration (if applicable)
TAX_SETTINGS = {
    'ENABLE_TAX': True,
    'TAX_RATE': Decimal('0.00'),  # Set to your local tax rate
    'TAX_INCLUDED': False,  # Whether tax is included in displayed prices
}
