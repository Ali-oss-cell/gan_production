from decimal import Decimal
from django.conf import settings

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    'SILVER': {
        'name': 'Silver',
        'price': Decimal('99.00'),  # Yearly price in USD
        'features': [
            'Profile visible in search results',
            'Upload up to 4 profile pictures',
            'Upload up to 2 showcase videos',
            'Basic search functionality',
            'Email support',
        ],
        'stripe_price_id': 'price_1RfJFoP623EsFG0oJbcWJKzU',
        'duration_months': 12,
    },
    'GOLD': {
        'name': 'Gold',
        'price': Decimal('199.00'),  # Yearly price in USD
        'features': [
            'Enhanced profile visibility in search',
            'Upload up to 5 profile pictures',
            'Upload up to 3 showcase videos',
            'Enhanced search optimization',
            'Email and phone support',
        ],
        'stripe_price_id': 'price_1RfJjxP623EsFG0oZvEjMoiP',
        'duration_months': 12,
    },
    'PLATINUM': {
        'name': 'Platinum',
        'price': Decimal('350.00'),  # Yearly price in USD
        'features': [
            'Maximum profile visibility in search',
            'Upload up to 6 profile pictures',
            'Upload up to 4 showcase videos',
            'VIP search optimization',
            'Priority email and phone support',
        ],
        'stripe_price_id': 'price_1RfJkoP623EsFG0oN96YwLf9',
        'duration_months': 12,
    },
    'BANDS': {
        'name': 'Bands',
        'price': Decimal('500.00'),  # Yearly price in USD
        'features': [
            'Special band profile layout',
            'Upload up to 5 band pictures',
            'Upload up to 5 band videos',
            'Band member management',
            'Event calendar integration',
            'Priority booking requests',
            'Dedicated band support',
        ],
        'stripe_price_id': 'price_1RfJmOP623EsFG0o16QVjMut',  # Bands plan price ID
        'duration_months': 12,
    },
    'BACKGROUND_JOBS': {
        'name': 'Production Assets Pro',
        'price': Decimal('300.00'),  # Yearly price in USD
        'features': [
            'Create and share props, costumes, locations, vehicles',
            'Rent and sell items to production companies',
            'Upload unlimited media files for your items',
            'Create detailed listings with descriptions and pricing',
            'Respond to job requests and booking inquiries',
            'Priority listing in search results',
            'Direct communication with production companies',
            'Professional profile with enhanced visibility',
            'Dedicated support for equipment services',
        ],
        'stripe_price_id': 'price_1RfJnhP623EsFG0onn7GnIYh',
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
