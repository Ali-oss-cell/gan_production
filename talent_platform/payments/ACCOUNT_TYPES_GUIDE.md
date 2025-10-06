# Account Types and Payment Features Guide

## Overview
This guide explains the different account types available in the talent platform and their associated features and pricing.

## Account Types

### 1. Free Account
- **Cost**: $0/month
- **Media Limits**: 2 images, 1 video
- **Features**:
  - Basic profile creation
  - Limited media uploads
  - Basic search visibility
  - Standard support

### 2. Premium Account
- **Cost**: $8.33/month ($99.99/year)
- **Media Limits**: 4 images, 2 videos
- **Features**:
  - Enhanced profile visibility
  - Boosted search ranking
  - Profile verification
  - Priority support
  - Basic analytics
  - Social media integration
  - Enhanced profile features

### 3. Platinum Account
- **Cost**: $16.67/month ($199.99/year)
- **Media Limits**: 6 images, 4 videos
- **Features**:
  - Premium profile visibility
  - Highest search ranking
  - Profile verification
  - Priority support
  - Advanced analytics
  - Social media integration
  - Featured profile placement
  - Custom profile URL
  - Advanced search filters

### 4. Bands Account
- **Cost**: $12.50/month ($149.99/year)
- **Features**:
  - Create and manage bands
  - Unlimited member invitations
  - Band media uploads (5 images, 5 videos)
  - Band analytics
  - Priority support
  - Band management tools

### 5. Background Jobs Professional
- **Cost**: $20.83/month ($249.99/year)
- **Features**:
  - Unlimited job postings
  - Applicant tracking
  - Advanced analytics
  - Priority support
  - Background verification
  - Unlimited item management

## Payment Processing

### Supported Payment Methods
- Credit/Debit Cards (Visa, Mastercard, American Express, Discover)
- Apple Pay (iOS devices)
- Google Pay (Android devices)
- PayPal
- Bank Transfer
- Regional payment methods (SEPA, iDEAL, etc.)

### Billing
- All subscriptions are billed annually
- Automatic renewal
- Cancel anytime
- Prorated refunds for unused time

## Account Upgrades/Downgrades

### Upgrade Process
1. User selects new plan
2. Payment processed via Stripe
3. Account type updated immediately
4. New features activated

### Downgrade Process
1. User cancels current subscription
2. Account reverts to Free at end of billing period
3. Premium features disabled
4. Media limits enforced

## Admin Management

### Admin Actions Available
- **Upgrade to Premium**: Change user account type to premium
- **Upgrade to Platinum**: Change user account type to platinum
- **Downgrade to Free**: Change user account type to free
- **Approve Users**: Approve restricted country users
- **Reject Users**: Reject restricted country users

### Bulk Operations
- Select multiple users
- Apply account type changes in bulk
- Track changes with admin user attribution

## Technical Implementation

### Database Fields
- `account_type`: CharField with choices (free, premium, platinum)
- `subscription`: ForeignKey to Subscription model
- `stripe_customer_id`: Stripe customer reference
- `stripe_subscription_id`: Stripe subscription reference

### Media Limits Enforcement
```python
def can_upload_image(self):
    return self.media.filter(media_type='image').count() < self.get_image_limit()

def get_image_limit(self):
    limits = {
        'free': 2,
        'premium': 4,
        'platinum': 6
    }
    return limits.get(self.account_type, 0)
```

### Search Ranking
```python
# Account type affects search ranking
if profile.account_type == 'platinum':
    score += 15  # Highest boost
elif profile.account_type == 'premium':
    score += 10  # Medium boost
# Free accounts get no boost
```

## Environment Variables

### Required Stripe Configuration
```bash
STRIPE_PUBLIC_KEY=pk_live_your-stripe-public-key
STRIPE_SECRET_KEY=sk_live_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Price IDs
STRIPE_PRICE_PREMIUM=price_your-premium-price-id
STRIPE_PRICE_PLATINUM=price_your-platinum-price-id
STRIPE_PRICE_BACKGROUND_JOBS=price_your-background-jobs-price-id
STRIPE_PRICE_BANDS=price_your-bands-price-id
```

## Migration Notes

### From Old System (Gold/Silver)
- Gold users → Premium users
- Silver users → Premium users
- Platinum users → Platinum users (unchanged)
- Free users → Free users (unchanged)

### Data Migration
```python
# Convert existing users
TalentUserProfile.objects.filter(account_type='gold').update(account_type='premium')
TalentUserProfile.objects.filter(account_type='silver').update(account_type='premium')
```

## Support and Troubleshooting

### Common Issues
1. **Payment Failures**: Check Stripe logs and user payment method
2. **Account Type Not Updating**: Verify subscription status and webhook processing
3. **Media Upload Limits**: Check account type and current media count
4. **Search Ranking**: Verify account type and profile completeness

### Monitoring
- Track subscription metrics
- Monitor payment success rates
- Track account type distribution
- Monitor feature usage by account type
