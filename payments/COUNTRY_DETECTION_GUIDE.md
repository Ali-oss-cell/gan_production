# 🌍 Country Detection for Payment Methods

This guide explains how the system automatically detects a user's country to show appropriate payment methods.

## 🎯 How It Works

The system uses a **multi-layered approach** to detect the user's country:

### 1. **User Profile Country** (Primary - Most Accurate)
- **Source**: `user.talent_user.country` or `user.background_profile.country`
- **Accuracy**: 100% if user set it correctly
- **Priority**: Highest

### 2. **IP Address Detection** (Fallback)
- **Source**: Free IP geolocation service (ip-api.com)
- **Accuracy**: ~95%
- **Priority**: Medium
- **Rate Limit**: 1000 requests/day (free tier)

### 3. **Browser Language** (Fallback)
- **Source**: HTTP `Accept-Language` header
- **Accuracy**: ~60%
- **Priority**: Low

### 4. **Default to UAE** (Final Fallback)
- **Source**: Hardcoded default
- **Accuracy**: N/A
- **Priority**: Lowest

## 🔧 Implementation

### API Usage

```python
# Automatic country detection
POST /api/payments/subscriptions/create_checkout_session/
{
    "plan_id": 1,
    "success_url": "https://yoursite.com/success",
    "cancel_url": "https://yoursite.com/cancel"
}

# Response includes detected country and payment methods
{
    "session_id": "cs_xxx",
    "url": "https://checkout.stripe.com/xxx",
    "detected_region": "ae",
    "payment_methods": ["card", "apple_pay", "google_pay", "paypal", "mada", "unionpay"]
}
```

### Manual Override

```python
# Override detected country
POST /api/payments/subscriptions/create_checkout_session/
{
    "plan_id": 1,
    "success_url": "https://yoursite.com/success",
    "cancel_url": "https://yoursite.com/cancel",
    "region_code": "us"  # Force US payment methods
}
```

## 🌍 Supported Countries & Payment Methods

### UAE (ae)
- Credit/Debit Cards
- Apple Pay
- Google Pay
- PayPal
- Mada (Saudi cards)
- UnionPay (Chinese cards)

### United States (us)
- Credit/Debit Cards
- Apple Pay
- Google Pay
- PayPal
- Afterpay
- Klarna
- Bank Transfer

### United Kingdom (gb)
- Credit/Debit Cards
- Apple Pay
- Google Pay
- PayPal
- Klarna
- Afterpay

### Europe (eu)
- Credit/Debit Cards
- Apple Pay
- Google Pay
- PayPal
- SEPA Direct Debit
- Klarna

### Saudi Arabia (sa)
- Credit/Debit Cards
- Apple Pay
- Google Pay
- PayPal
- Mada

### China (cn)
- Credit/Debit Cards
- Alipay
- WeChat Pay

## 🛠️ Configuration

### Country Code Mapping

The system includes a comprehensive mapping of country names to ISO codes:

```python
COUNTRY_CODE_MAPPING = {
    'united states': 'us',
    'usa': 'us',
    'uae': 'ae',
    'united arab emirates': 'ae',
    'uk': 'gb',
    'united kingdom': 'gb',
    # ... 200+ countries
}
```

### Regional Payment Preferences

```python
REGIONAL_PREFERENCES = {
    'ae': ['card', 'apple_pay', 'google_pay', 'paypal', 'mada', 'unionpay'],
    'us': ['card', 'apple_pay', 'google_pay', 'paypal', 'afterpay', 'klarna'],
    'gb': ['card', 'apple_pay', 'google_pay', 'paypal', 'klarna', 'afterpay'],
    'global': ['card', 'paypal'],
}
```

## 🧪 Testing

### Run Country Detection Test

```bash
cd talent_platform
python payments/test_country_detection.py
```

### Test Output Example

```
🌍 Testing Country Detection for Payment Methods
============================================================

1. Country Code Mapping Tests:
   ✅ UAE -> ae (expected: ae)
   ✅ United States -> us (expected: us)
   ✅ UK -> gb (expected: gb)

2. Payment Methods by Region:
   AE: ['card', 'paypal', 'mada', 'unionpay']
   US: ['card', 'paypal', 'afterpay', 'klarna']
   GB: ['card', 'paypal', 'klarna', 'afterpay']

3. User Profile Country Detection:
   test_uae@example.com:
      Profile Country: UAE
      Detected Country: ae
      Payment Methods: ['card', 'paypal', 'mada', 'unionpay']
```

## 🔒 Security & Privacy

### IP Detection
- Uses free, public IP geolocation service
- No personal data stored
- Rate limited to prevent abuse
- Falls back gracefully if service unavailable

### User Privacy
- Country detection is non-intrusive
- Users can override detected country
- No tracking or profiling
- Respects user privacy preferences

## 🚀 Performance

### Caching Strategy
- IP detection results can be cached (future enhancement)
- User profile country is cached in database
- Browser language detection is fast and local

### Fallback Strategy
- Multiple detection methods ensure reliability
- Graceful degradation if services unavailable
- Always provides payment methods (defaults to UAE)

## 📝 Troubleshooting

### Common Issues

1. **Wrong Country Detected**
   - Check user profile country field
   - Verify IP geolocation accuracy
   - Use manual override if needed

2. **No Payment Methods Showing**
   - Check Stripe payment method configuration
   - Verify regional preferences mapping
   - Ensure Stripe account supports methods

3. **IP Detection Failing**
   - Check network connectivity
   - Verify IP geolocation service status
   - Check rate limits

### Debug Information

The API response includes debug information:

```json
{
    "session_id": "cs_xxx",
    "url": "https://checkout.stripe.com/xxx",
    "detected_region": "ae",
    "payment_methods": ["card", "apple_pay", "google_pay", "paypal", "mada", "unionpay"]
}
```

## 🔄 Future Enhancements

1. **Caching**: Cache IP detection results
2. **More Services**: Add paid IP geolocation services
3. **User Preferences**: Allow users to set preferred payment methods
4. **Analytics**: Track payment method usage by region
5. **Dynamic Pricing**: Adjust pricing based on region

## 📞 Support

For issues with country detection or payment methods:

1. Check the test output for errors
2. Verify user profile country settings
3. Test with manual region override
4. Check Stripe dashboard configuration
5. Review server logs for API errors 