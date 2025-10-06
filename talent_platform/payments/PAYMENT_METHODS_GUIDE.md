# Payment Methods Implementation Guide

## Overview

This guide explains how to implement and use the enhanced payment methods system that supports Apple Pay, Google Pay, PayPal, and other modern payment methods.

## New Payment Methods Added

### Digital Wallets
- **Apple Pay** - iOS devices
- **Google Pay** - Android devices
- **PayPal** - Global support

### Regional Payment Methods
- **SEPA Direct Debit** - European Union
- **Bank Transfer (ACH)** - United States
- **Alipay** - China
- **WeChat Pay** - China

### Buy Now, Pay Later
- **Afterpay** - US, Canada, Australia, UK
- **Klarna** - US, EU, UK, Australia

## Database Changes

### New Model: PaymentMethodSupport

This model tracks which payment methods are supported in different regions:

```python
class PaymentMethodSupport(models.Model):
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    region = models.CharField(max_length=10, choices=REGION_CHOICES)
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    processing_fee = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stripe_payment_method_type = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
```

### Updated PaymentTransaction Model

Enhanced with new payment method choices:

```python
PAYMENT_METHOD_CHOICES = [
    ('card', 'Credit/Debit Card'),
    ('apple_pay', 'Apple Pay'),
    ('google_pay', 'Google Pay'),
    ('paypal', 'PayPal'),
    ('bank_transfer', 'Bank Transfer'),
    ('sepa_debit', 'SEPA Direct Debit'),
    ('alipay', 'Alipay'),
    ('wechat_pay', 'WeChat Pay'),
    ('afterpay', 'Afterpay'),
    ('klarna', 'Klarna'),
    # ... and more
]
```

## Setup Instructions

### 1. Run Migrations

```bash
python manage.py makemigrations payments
python manage.py migrate
```

### 2. Set Up Payment Methods

```bash
# Set up all payment methods for all regions
python manage.py setup_payment_methods

# Set up specific region
python manage.py setup_payment_methods --region us

# Set up specific payment method
python manage.py setup_payment_methods --method apple_pay

# Clear existing data and start fresh
python manage.py setup_payment_methods --clear
```

### 3. Configure Stripe Settings

Add these to your `settings.py`:

```python
# Stripe Configuration
STRIPE_SECRET_KEY = 'your_stripe_secret_key'
STRIPE_PUBLISHABLE_KEY = 'your_stripe_publishable_key'
STRIPE_MERCHANT_NAME = 'Your Company Name'
STRIPE_MERCHANT_ID = 'your_merchant_id'

# Apple Pay Configuration
APPLE_PAY_MERCHANT_ID = 'merchant.com.yourcompany.app'

# Payment Method IDs (from Stripe Dashboard)
STRIPE_PREMIUM_PRICE_ID = 'price_xxx'
STRIPE_PLATINUM_PRICE_ID = 'price_xxx'
STRIPE_BANDS_PRICE_ID = 'price_xxx'
STRIPE_BACKGROUND_JOBS_PRICE_ID = 'price_xxx'
```

## API Endpoints

### Get Available Payment Methods

```http
GET /api/payments/methods/?amount=150.00&currency=USD
```

Response:
```json
{
    "region": "us",
    "currency": "USD",
    "payment_methods": [
        {
            "method": "card",
            "name": "Credit/Debit Card",
            "min_amount": 0.5,
            "max_amount": 999999.99,
            "processing_fee": 2.9,
            "fixed_fee": 0.3,
            "description": "Visa, Mastercard, American Express, Discover",
            "stripe_type": "card"
        },
        {
            "method": "apple_pay",
            "name": "Apple Pay",
            "min_amount": 0.5,
            "max_amount": 999999.99,
            "processing_fee": 2.9,
            "fixed_fee": 0.3,
            "description": "Apple Pay for iOS devices",
            "stripe_type": "card"
        }
    ]
}
```

### Create Payment Intent

```http
POST /api/payments/create-intent/
Content-Type: application/json

{
    "amount": "150.00",
    "payment_method": "apple_pay",
    "currency": "USD",
    "metadata": {
        "plan": "premium",
        "user_id": "123"
    }
}
```

### Get Apple Pay Configuration

```http
GET /api/payments/apple-pay-config/
```

### Get Google Pay Configuration

```http
GET /api/payments/google-pay-config/
```

## Frontend Implementation

### Apple Pay Integration

```javascript
// Check if Apple Pay is available
if (window.ApplePaySession && ApplePaySession.canMakePayments()) {
    // Apple Pay is available
    const paymentRequest = {
        countryCode: 'US',
        currencyCode: 'USD',
        supportedNetworks: ['visa', 'mastercard', 'amex'],
        merchantCapabilities: ['supports3DS'],
        total: {
            label: 'Your Company',
            amount: '150.00'
        }
    };

    const session = new ApplePaySession(3, paymentRequest);
    
    session.onvalidatemerchant = function(event) {
        // Validate merchant with your server
        fetch('/api/payments/apple-pay-config/')
            .then(response => response.json())
            .then(config => {
                session.completeMerchantValidation(config);
            });
    };

    session.onpaymentauthorized = function(event) {
        // Process payment with your server
        const payment = event.payment;
        // Send to your backend for processing
        session.completePayment(ApplePaySession.STATUS_SUCCESS);
    };

    session.begin();
}
```

### Google Pay Integration

```javascript
// Load Google Pay API
const paymentsClient = new google.payments.api.PaymentsClient({
    environment: 'TEST' // or 'PRODUCTION'
});

// Get payment data request
const paymentDataRequest = {
    apiVersion: 2,
    apiVersionMinor: 0,
    allowedPaymentMethods: [{
        type: 'CARD',
        parameters: {
            allowedAuthMethods: ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
            allowedCardNetworks: ['VISA', 'MASTERCARD', 'AMEX'],
        },
        tokenizationSpecification: {
            type: 'PAYMENT_GATEWAY',
            parameters: {
                gateway: 'stripe',
                gatewayMerchantId: 'your_merchant_id',
            },
        },
    }],
    merchantInfo: {
        merchantName: 'Your Company',
    },
    transactionInfo: {
        totalPriceStatus: 'FINAL',
        totalPriceLabel: 'Total',
        totalPrice: '150.00',
        currencyCode: 'USD',
        countryCode: 'US',
    },
};

// Check if Google Pay is ready
paymentsClient.isReadyToPay(paymentDataRequest)
    .then(function(response) {
        if (response.result) {
            // Google Pay is ready
            const button = paymentsClient.createButton({
                onClick: onGooglePaymentButtonClicked
            });
            document.getElementById('google-pay-button').appendChild(button);
        }
    });

function onGooglePaymentButtonClicked() {
    paymentsClient.loadPaymentData(paymentDataRequest)
        .then(function(paymentData) {
            // Process payment with your server
            processPayment(paymentData);
        })
        .catch(function(err) {
            console.error(err);
        });
}
```

## Regional Support

### United States (US)
- Credit/Debit Cards
- Apple Pay
- Google Pay
- PayPal
- Bank Transfer (ACH)
- Afterpay
- Klarna

### European Union (EU)
- Credit/Debit Cards
- Apple Pay
- Google Pay
- PayPal
- SEPA Direct Debit
- Klarna

### China (CN)
- Credit/Debit Cards
- Alipay
- WeChat Pay

### Global
- Credit/Debit Cards
- PayPal

## Processing Fees

Each payment method has different processing fees:

- **Credit/Debit Cards**: 2.9% + $0.30
- **Apple Pay**: 2.9% + $0.30
- **Google Pay**: 2.9% + $0.30
- **PayPal**: 3.5% + $0.35
- **Bank Transfer**: 0.8% (no fixed fee)
- **SEPA Debit**: 0.8% (no fixed fee)
- **Afterpay**: 4.0% + $0.30
- **Klarna**: 3.5% + $0.30

## Security Considerations

1. **HTTPS Required**: All payment methods require HTTPS in production
2. **Domain Verification**: Apple Pay requires domain verification
3. **PCI Compliance**: Ensure your implementation follows PCI DSS guidelines
4. **Tokenization**: Use Stripe's tokenization for sensitive payment data
5. **Webhook Verification**: Verify webhook signatures from Stripe

## Testing

### Test Cards

Use Stripe's test card numbers:
- **Visa**: 4242424242424242
- **Mastercard**: 5555555555554444
- **American Express**: 378282246310005

### Test Payment Methods

- **Apple Pay**: Use Safari on macOS or iOS with test cards
- **Google Pay**: Use Chrome with test cards
- **PayPal**: Use PayPal Sandbox accounts

## Troubleshooting

### Common Issues

1. **Apple Pay not showing**: Ensure domain verification is complete
2. **Google Pay not working**: Check merchant ID configuration
3. **Payment declined**: Verify test card numbers and amounts
4. **Regional restrictions**: Check if payment method is supported in user's region

### Debug Mode

Enable debug logging in your Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'payments': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Next Steps

1. **Implement frontend components** for each payment method
2. **Add webhook handlers** for payment status updates
3. **Implement error handling** and user feedback
4. **Add payment method management** in user dashboard
5. **Set up monitoring** and analytics for payment methods
6. **Implement recurring payments** for subscriptions

## Support

For issues with:
- **Stripe Integration**: Check Stripe documentation
- **Apple Pay**: Refer to Apple Pay Developer Guide
- **Google Pay**: Check Google Pay API documentation
- **Regional Compliance**: Consult local payment regulations 