from decimal import Decimal
from django.conf import settings

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    'SILVER': {
        'name': 'Silver',
        'price': Decimal('150.00'),  # Yearly price in USD
        'features': [
            'Basic profile visibility',
            'Up to 4 picturs media uploads',
            'Up to 2 videos uplode'
            'Basic search functionality (we can find you)',
            'Email support (we will reach you in email)',
        ],
        'stripe_price_id': settings.STRIPE_SILVER_PRICE_ID,
        'duration_months': 12,
    },
    'GOLD': {
        'name': 'Gold',
        'price': Decimal('200.00'),  # Yearly price in USD
        'features': [
           'Ehanced profile visibility',
            'Up to 5 picturs media uploads',
            'Up to 3 videos uplode'
            'Ehanced search functionality (we are looking for YOU )',
            'Email support (we will reach you in Email or Phone)',
        ],
        'stripe_price_id': settings.STRIPE_GOLD_PRICE_ID,
        'duration_months': 12,
    },
    'PLATINUM': {
        'name': 'Platinum',
        'price': Decimal('300.00'),  # Yearly price in USD
        'features': [
           'primuem profile visibility',
            'Up to 5 picturs media uploads',
            'Up to 3 videos uplode'
            'Ehanced search functionality (we are looking for YOU )',
            'Email support (You are the Star of the show)',
        ],
        'stripe_price_id': settings.STRIPE_PLATINUM_PRICE_ID,
        'duration_months': 12,
    },
    'BANDS': {
        'name': 'Bands',
        'price': Decimal('350.00'),  # Yearly price in USD
        'features': [
            'Special band profile layout',
            'Up to 10 pictures media uploads',
            'Up to 5 videos upload',
            'Band member management',
            'Event calendar integration',
            'Music track uploads (up to 10 songs)',
            'Priority booking requests',
            'Dedicated band support',
        ],
        'stripe_price_id': settings.STRIPE_BANDS_PRICE_ID,
        'duration_months': 12,
    },
    'BACKGROUND_JOBS': {
        'name': 'Background Jobs',
        'price': Decimal('500.00'),  # Yearly price in USD
        'features': [
            'Access to background job processing services',
            'you will be able to share your rare items',
            'reant or seal any thing related to art and cenima',
            'this is the place where you able to share any cool things',
        ],
        'stripe_price_id': settings.STRIPE_BACKGROUND_JOBS_PRICE_ID,
        'duration_months': 12,
    },
}

# Additional Pricing Options
ADDITIONAL_SERVICES = {
    'PROFILE_VERIFICATION': {
        'name': 'Profile Verification',
        'price': Decimal('19.99'),
        'description': 'Get your profile verified by our team',
        'stripe_price_id': settings.STRIPE_VERIFICATION_PRICE_ID,
    },
    'FEATURED_PLACEMENT': {
        'name': 'Featured Placement',
        'price': Decimal('49.99'),
        'description': 'Get your profile featured for 7 days',
        'stripe_price_id': settings.STRIPE_FEATURED_PRICE_ID,
    },
    'CUSTOM_URL': {
        'name': 'Custom Profile URL',
        'price': Decimal('9.99'),
        'description': 'Get a custom URL for your profile',
        'stripe_price_id': settings.STRIPE_CUSTOM_URL_PRICE_ID,
    },
    'BANDS': {
        'name': 'Bands Package',
        'price': Decimal('350.00'),
        'description': 'Special package for bands and musical groups',
        'stripe_price_id': settings.STRIPE_BANDS_PRICE_ID,
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
