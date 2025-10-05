# Free vs Paid Plans Refactor - Implementation Guide

## Overview
This guide provides all the code changes needed to create a clear distinction between free and paid plans in the talent platform.

## Changes Summary
- **Free Plan**: 1 image, 0 videos, 5 messages/month, no analytics, no verification, low search visibility
- **Premium Plan**: 4 images, 2 videos, 50 messages/month, analytics, verification, enhanced search visibility
- **Platinum Plan**: 6 images, 4 videos, unlimited messages, all features, highest search visibility

---

## 1. Update Media Limits in `talent_platform/profiles/models.py`

### Find and update the `get_image_limit` method (around line 224):

```python
def get_image_limit(self):
    """
    Get the maximum number of images allowed based on account type.
    """
    limits = {
        'free': 1,        # Changed from 2 to 1 - Very limited for free users
        'premium': 4,
        'platinum': 6
    }
    return limits.get(self.account_type, 0)
```

### Find and update the `get_video_limit` method (around line 235):

```python
def get_video_limit(self):
    """
    Get the maximum number of videos allowed based on account type.
    """
    limits = {
        'free': 0,        # Changed from 1 to 0 - No videos for free users
        'premium': 2,
        'platinum': 4
    }
    return limits.get(self.account_type, 0)
```

---

## 2. Add New Restriction Methods to `TalentUserProfile` Class

### Add these methods before the `class Meta` line (around line 304):

```python
def get_message_limit(self):
    """
    Get the maximum number of messages allowed per month based on account type.
    """
    limits = {
        'free': 5,           # Very limited messaging
        'premium': 50,       # Moderate messaging
        'platinum': -1       # Unlimited (-1 means unlimited)
    }
    return limits.get(self.account_type, 5)

def can_access_analytics(self):
    """
    Check if user can access analytics dashboard.
    """
    return self.account_type in ['premium', 'platinum']

def can_verify_profile(self):
    """
    Check if user can verify their profile.
    """
    return self.account_type in ['premium', 'platinum']

def can_use_advanced_search(self):
    """
    Check if user can use advanced search filters.
    """
    return self.account_type in ['premium', 'platinum']

def can_get_priority_support(self):
    """
    Check if user gets priority support.
    """
    return self.account_type in ['premium', 'platinum']

def get_search_boost(self):
    """
    Get search ranking boost multiplier.
    """
    boosts = {
        'free': 0.1,          # Very low visibility
        'premium': 0.5,       # Medium visibility  
        'platinum': 1.0       # High visibility
    }
    return boosts.get(self.account_type, 0.1)

def can_create_custom_url(self):
    """
    Check if user can create custom profile URL.
    """
    return self.account_type == 'platinum'

def can_get_featured_placement(self):
    """
    Check if user can get featured profile placement.
    """
    return self.account_type == 'platinum'

def get_upgrade_benefits(self):
    """
    Get benefits that would be unlocked with upgrade.
    """
    if self.account_type == 'free':
        return {
            'media': {
                'current': f"{self.get_image_limit()} image(s), {self.get_video_limit()} video(s)",
                'premium': "4 images, 2 videos",
                'platinum': "6 images, 4 videos"
            },
            'messaging': {
                'current': f"{self.get_message_limit()} messages/month",
                'premium': "50 messages/month", 
                'platinum': "Unlimited messages"
            },
            'features': {
                'current': "Basic profile only",
                'premium': "Verification badge, Analytics, Priority support",
                'platinum': "All Premium features + Featured placement, Custom URL"
            },
            'visibility': {
                'current': "Low search visibility (10% boost)",
                'premium': "Enhanced visibility (50% boost)",
                'platinum': "Highest visibility (100% boost) + Featured placement"
            }
        }
    elif self.account_type == 'premium':
        return {
            'platinum_upgrade': {
                'additional_media': "2 more images, 2 more videos",
                'messaging': "Unlimited messages",
                'features': "Featured placement, Custom URL",
                'visibility': "Highest visibility + Featured placement"
            }
        }
    return {}

def get_account_badge(self):
    """
    Get account type badge for display.
    """
    badges = {
        'free': {'text': 'Free', 'color': 'gray', 'icon': 'basic'},
        'premium': {'text': 'Premium', 'color': 'blue', 'icon': 'star'},
        'platinum': {'text': 'Platinum', 'color': 'gold', 'icon': 'crown'}
    }
    return badges.get(self.account_type, badges['free'])
```

---

## 3. Update Pricing Configuration in `talent_platform/payments/pricing_config.py`

### Update the features lists for PREMIUM and PLATINUM plans:

```python
SUBSCRIPTION_PLANS = {
    'PREMIUM': {
        'name': 'Premium',
        'price': Decimal('19.99'),  # Yearly price in USD
        'features': [
            'Upload up to 4 profile pictures',
            'Upload up to 2 showcase videos', 
            '50 messages per month',
            'Enhanced search visibility (50% boost)',
            'Profile verification badge',
            'Basic analytics dashboard',
            'Priority support',
            'Social media integration',
            'Advanced search filters'
        ],
        'stripe_price_id': 'price_premium',
        'duration_months': 12,
    },
    'PLATINUM': {
        'name': 'Platinum', 
        'price': Decimal('39.99'),  # Yearly price in USD
        'features': [
            'Upload up to 6 profile pictures',
            'Upload up to 4 showcase videos',
            'Unlimited messages',
            'Highest search visibility (100% boost)',
            'Profile verification badge',
            'Advanced analytics dashboard',
            'Priority support',
            'Social media integration',
            'All search filters',
            'Featured profile placement',
            'Custom profile URL',
            'VIP treatment'
        ],
        'stripe_price_id': 'price_platinum',
        'duration_months': 12,
    },
    # Keep BANDS and BACKGROUND_JOBS as they are
}
```

---

## 4. Update Serializers in `talent_platform/profiles/talent_profile_serializers.py`

### Update the `TalentUserProfileSerializer` class:

#### Add new fields to the class (after line 86):

```python
class TalentUserProfileSerializer(serializers.ModelSerializer):
    media = TalentMediaSerializer(many=True, read_only=True)
    social_media_links = SocialMediaLinksSerializer(read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email_verified = serializers.BooleanField(source='user.email_verified', read_only=True)
    full_name = serializers.SerializerMethodField()
    profile_score = serializers.SerializerMethodField()
    
    # ADD THESE NEW FIELDS:
    upgrade_prompt = serializers.SerializerMethodField()
    account_limitations = serializers.SerializerMethodField()
    account_badge = serializers.SerializerMethodField()
```

#### Update the fields list in Meta:

```python
    class Meta:
        model = TalentUserProfile
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name', 'email_verified', 'is_verified', 'profile_complete',
            'account_type', 'country', 'residency', 'city','phone', 'profile_picture', 'aboutyou',
            'date_of_birth', 'gender', 'media', 'social_media_links', 'aboutyou', 'profile_score',
            'upgrade_prompt', 'account_limitations', 'account_badge'  # ADD THESE
        ]
```

#### Add these new methods (after `get_profile_score`):

```python
    def get_upgrade_prompt(self, obj):
        """Get upgrade prompt for free users"""
        if obj.account_type == 'free':
            return {
                'message': 'Upgrade to unlock more features!',
                'benefits': obj.get_upgrade_benefits(),
                'upgrade_url': '/pricing'
            }
        elif obj.account_type == 'premium':
            return {
                'message': 'Upgrade to Platinum for maximum visibility!',
                'benefits': obj.get_upgrade_benefits(),
                'upgrade_url': '/pricing'
            }
        return None
    
    def get_account_limitations(self, obj):
        """Get current account limitations"""
        image_count = obj.media.filter(media_type='image').count()
        video_count = obj.media.filter(media_type='video').count()
        
        return {
            'images_used': image_count,
            'images_limit': obj.get_image_limit(),
            'images_remaining': max(0, obj.get_image_limit() - image_count),
            'videos_used': video_count,
            'videos_limit': obj.get_video_limit(),
            'videos_remaining': max(0, obj.get_video_limit() - video_count),
            'messages_limit': obj.get_message_limit(),
            'can_verify': obj.can_verify_profile(),
            'can_analytics': obj.can_access_analytics(),
            'can_advanced_search': obj.can_use_advanced_search(),
            'can_priority_support': obj.can_get_priority_support(),
            'can_custom_url': obj.can_create_custom_url(),
            'can_featured_placement': obj.can_get_featured_placement()
        }
    
    def get_account_badge(self, obj):
        """Get account type badge for display"""
        return obj.get_account_badge()
```

---

## 5. Update Search Ranking in `talent_platform/dashboard/search_views.py`

### Find the `calculate_relevance_score` method and add account boost:

Add this code after the base score calculation (look for where the score is calculated):

```python
def calculate_relevance_score(self, profile, query_terms):
    # ... existing score calculation ...
    
    # Apply account type boost
    account_boost = profile.get_search_boost()
    score = score * (1 + account_boost)
    
    # Additional boost for verified profiles (paid only)
    if profile.is_verified and profile.account_type != 'free':
        score += 20
    
    # Platinum users get featured placement boost
    if profile.can_get_featured_placement():
        score += 10
    
    return score
```

---

## 6. Create Documentation

### Create `talent_platform/payments/FREE_PLAN_FEATURES.md`:

```markdown
# Free Plan Features and Limitations

## Free Plan Limits
- 1 profile picture only
- 0 videos allowed
- 5 messages per month
- Basic profile visibility (10% search boost)
- No profile verification badge
- No analytics dashboard
- No advanced search filters
- No priority support

## Upgrade Benefits

### Premium Plan ($19.99/year)
- 4 profile pictures
- 2 showcase videos
- 50 messages per month
- Enhanced visibility (50% search boost)
- Profile verification badge
- Basic analytics dashboard
- Priority support
- Advanced search filters

### Platinum Plan ($39.99/year)
- 6 profile pictures
- 4 showcase videos
- Unlimited messages
- Highest visibility (100% search boost)
- Profile verification badge
- Advanced analytics dashboard
- Priority support
- Featured profile placement
- Custom profile URL
- VIP treatment
```

---

## 7. Testing Checklist

After implementing these changes:

- [ ] Verify free users can only upload 1 image
- [ ] Verify free users cannot upload videos
- [ ] Check upgrade prompts appear for free users
- [ ] Test that analytics is blocked for free users
- [ ] Test that verification is blocked for free users
- [ ] Verify search ranking boost is applied correctly
- [ ] Test serializer returns new fields correctly
- [ ] Verify pricing page reflects new features
- [ ] Test API responses include limitation data

---

## Implementation Order

1. **Start with models.py** - Update media limits and add restriction methods
2. **Update pricing_config.py** - Update features lists
3. **Update serializers.py** - Add new fields and methods
4. **Update search_views.py** - Add search boost logic
5. **Test the changes** - Verify all restrictions work correctly

---

## Notes

- Free users will now have significantly limited features, encouraging upgrades
- The distinction between plans is now very clear
- Search visibility is directly tied to account type
- All restriction methods are centralized in the model
- Serializers expose all limitation data to the frontend

---

## Support

If you encounter any issues during implementation, check:
1. Django migrations are up to date
2. All imports are correct
3. Method signatures match existing code
4. No circular import issues

## End of Implementation Guide

