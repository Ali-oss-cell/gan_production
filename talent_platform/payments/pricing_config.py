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
            'Basic profile features'
        ],
        'stripe_price_id': 'price_free',
        'duration_months': 12,
    },
    'PREMIUM': {
        'name': 'Premium',
        'price': Decimal('99.99'),  # Yearly price in USD
        'features': [
            'Upload up to 4 profile pictures',
            'Upload up to 2 showcase videos',
            'Enhanced search visibility (50% boost)',
            'Profile verification badge'
        ],
        'stripe_price_id': getattr(settings, 'STRIPE_PRICE_IDS', {}).get('premium', 'price_premium'),
        'duration_months': 12,
        'monthly_equivalent': Decimal('8.33')
    },
    'PLATINUM': {
        'name': 'Platinum', 
        'price': Decimal('199.99'),  # Yearly price in USD
        'features': [
            'Upload up to 6 profile pictures',
            'Upload up to 4 showcase videos',
            'Highest search visibility (100% boost)',
            'Profile verification badge',
            'Featured profile placement',
            'Custom profile URL'
        ],
        'stripe_price_id': getattr(settings, 'STRIPE_PRICE_IDS', {}).get('platinum', 'price_platinum'),
        'duration_months': 12,
        'monthly_equivalent': Decimal('16.67')
    },
    'BANDS': {
        'name': 'Bands',
        'price': Decimal('149.99'),  # Yearly price in USD
        'features': [
            'Create and manage bands',
            'Unlimited member invitations',
            'Band media uploads (5 images, 5 videos)',
            'Band management tools'
        ],
        'stripe_price_id': getattr(settings, 'STRIPE_PRICE_IDS', {}).get('bands', 'price_bands'),
        'duration_months': 12,
        'monthly_equivalent': Decimal('12.50')
    },
    'BACKGROUND_JOBS': {
        'name': 'Background Jobs Professional',
        'price': Decimal('249.99'),  # Yearly price in USD
        'features': [
            'Create and manage props',
            'Create and manage costumes', 
            'Create and manage locations',
            'Create and manage memorabilia',
            'Create and manage vehicles',
            'Create and manage artistic materials',
            'Create and manage music items',
            'Create and manage rare items',
            'Rent and sell items',
            'Share items with other users'
        ],
        'stripe_price_id': getattr(settings, 'STRIPE_PRICE_IDS', {}).get('background_jobs', 'price_background'),
        'duration_months': 12,
        'monthly_equivalent': Decimal('20.83')
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
        'duration_days': None,
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

# Currency object to match your structure
CURRENCY_CONFIG = {
    'code': 'USD',
    'symbol': '$'
}

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
