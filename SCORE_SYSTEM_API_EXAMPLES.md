# Score System API Examples with Arabic Translations

## How Frontend Gets Arabic Translations

The Arabic translations are automatically included in all API responses that return profile scores. Here are the key API endpoints and their responses:

## 1. Talent Profile API

### Endpoint: `GET /api/profile/talent/`

**Response Example:**
```json
{
  "id": 123,
  "email": "talent@example.com",
  "username": "talent@example.com",
  "first_name": "Ahmed",
  "last_name": "Ali",
  "full_name": "Ahmed Ali",
  "email_verified": true,
  "is_verified": true,
  "profile_complete": true,
  "account_type": "premium",
  "country": "UAE",
  "city": "Dubai",
  "phone": "+971501234567",
  "profile_picture": "https://cdn.example.com/profile.jpg",
  "aboutyou": "Professional actor with 5 years experience",
  "profile_score": {
    "total": 85,
    "account_tier": 15,
    "verification": 25,
    "profile_completion": 20,
    "media_content": 15,
    "specialization": 10,
    "social_media": 0,
    "details": {
      "account_tier": "Premium account: +15 points",
      "verification": "Verified profile: +25 points",
      "profile_completion": "About section: +5 points; Profile picture: +5 points; Country specified: +3 points; Date of birth: +2 points; Specialization added: +10 points",
      "media_content": "Good portfolio (2-3 items): +10 points",
      "specialization": "Specializations: Visual Worker (+10 points)",
      "social_media": "No social media links: +0 points (add social links for up to +10 points)"
    },
    "details_ar": {
      "account_tier": "حساب بريميوم: +15 نقطة",
      "verification": "ملف شخصي موثق: +25 نقطة",
      "profile_completion": "قسم نبذة عني: +5 نقاط; صورة الملف الشخصي: +5 نقاط; البلد محدد: +3 نقاط; تاريخ الميلاد: +2 نقطة; تم إضافة التخصص: +10 نقاط",
      "media_content": "محفظة جيدة (2-3 عناصر): +10 نقاط",
      "specialization": "التخصصات: عامل بصري (+10 نقاط)",
      "social_media": "لا توجد روابط وسائل التواصل: +0 نقطة (أضف روابط وسائل التواصل لـ +10 نقاط)"
    },
    "improvement_tips": [
      "Add social media links for up to +10 points"
    ],
    "improvement_tips_ar": [
      "أضف روابط وسائل التواصل لـ +10 نقاط"
    ]
  },
  "media": [...],
  "social_media_links": {...}
}
```

## 2. Background Jobs Profile API

### Endpoint: `GET /api/profile/background/`

**Response Example:**
```json
{
  "id": 456,
  "email": "background@example.com",
  "username": "background@example.com",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "full_name": "Sarah Johnson",
  "country": "USA",
  "date_of_birth": "1985-05-15",
  "gender": "Female",
  "account_type": "back_ground_jobs",
  "profile_score": {
    "total": 70,
    "account_tier": 25,
    "profile_completion": 15,
    "item_diversity": 20,
    "item_quantity": 10,
    "details": {
      "account_tier": "All accounts paid: +25 points",
      "profile_completion": "Profile complete: +15 points",
      "item_diversity": "4 item types: +20 points",
      "item_quantity": "Small collection (5-10 items): +15 points"
    },
    "details_ar": {
      "account_tier": "جميع الحسابات مدفوعة: +25 نقطة",
      "profile_completion": "الملف الشخصي مكتمل: +15 نقطة",
      "item_diversity": "4 أنواع عناصر: +20 نقطة",
      "item_quantity": "مجموعة صغيرة (5-10 عناصر): +15 نقطة"
    }
  }
}
```

## 3. Band Profile API

### Endpoint: `GET /api/profile/bands/`

**Response Example:**
```json
{
  "bands": [
    {
      "id": 789,
      "name": "Rock Stars",
      "description": "Professional rock band",
      "band_type": "musical",
      "profile_picture": "https://cdn.example.com/band.jpg",
      "contact_email": "band@example.com",
      "contact_phone": "+971501234567",
      "location": "Dubai, UAE",
      "creator_name": "Ahmed Ali",
      "members": [...],
      "profile_score": {
        "total": 90,
        "profile_completion": 30,
        "media_content": 30,
        "member_count": 20,
        "band_details": 10,
        "details": {
          "profile_completion": "Complete band profile: +30 points",
          "media_content": "Maximum media (6 items): +30 points",
          "member_count": "Medium band (5-9 members): +20 points",
          "band_details": "All members have positions: +10 points"
        },
        "details_ar": {
          "profile_completion": "ملف الفرقة مكتمل: +30 نقطة",
          "media_content": "أقصى وسائط (6 عناصر): +30 نقطة",
          "member_count": "فرقة متوسطة (5-9 أعضاء): +20 نقطة",
          "band_details": "جميع الأعضاء لديهم مناصب: +10 نقاط"
        },
        "improvement_tips": [],
        "improvement_tips_ar": []
      }
    }
  ],
  "band_score": {
    "overall_score": 90,
    "has_bands_subscription": true,
    "user_role": "creator",
    "score_breakdown": {
      "base_score": 60,
      "subscription_bonus": 40,
      "profile_completion_bonus": 20,
      "details": {
        "profile_completion": "Complete band profile: +30 points",
        "media_content": "Maximum media (6 items): +30 points",
        "member_count": "Medium band (5-9 members): +20 points",
        "band_details": "All members have positions: +10 points"
      }
    },
    "how_to_improve": [
      "Your band profile is excellent! Keep engaging with the community."
    ],
    "message": "You are a creator of 'Rock Stars' band"
  }
}
```

## Frontend Implementation Examples

### React/JavaScript Example

```javascript
// Get profile data
const response = await fetch('/api/profile/talent/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const profileData = await response.json();
const scoreData = profileData.profile_score;

// Use Arabic translations based on user language preference
const userLanguage = localStorage.getItem('language') || 'en';
const isArabic = userLanguage === 'ar';

// Display score details
const scoreDetails = isArabic ? scoreData.details_ar : scoreData.details;
const improvementTips = isArabic ? scoreData.improvement_tips_ar : scoreData.improvement_tips;

// Example: Display account tier
const accountTierText = scoreDetails.account_tier;
// Arabic: "حساب بريميوم: +15 نقطة"
// English: "Premium account: +15 points"

// Example: Display improvement tips
improvementTips.forEach(tip => {
  console.log(tip);
  // Arabic: "أضف روابط وسائل التواصل لـ +10 نقاط"
  // English: "Add social media links for up to +10 points"
});
```

### Vue.js Example

```vue
<template>
  <div class="score-details">
    <h3>{{ $t('profile.score.title') }}</h3>
    <div class="score-breakdown">
      <div v-for="(value, key) in scoreDetails" :key="key" class="score-item">
        <span class="score-label">{{ getScoreLabel(key) }}</span>
        <span class="score-value">{{ value }}</span>
      </div>
    </div>
    
    <div v-if="improvementTips.length > 0" class="improvement-tips">
      <h4>{{ $t('profile.score.improvement') }}</h4>
      <ul>
        <li v-for="tip in improvementTips" :key="tip">{{ tip }}</li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  computed: {
    scoreDetails() {
      const isArabic = this.$i18n.locale === 'ar';
      return isArabic ? this.profileScore.details_ar : this.profileScore.details;
    },
    improvementTips() {
      const isArabic = this.$i18n.locale === 'ar';
      return isArabic ? this.profileScore.improvement_tips_ar : this.profileScore.improvement_tips;
    }
  }
}
</script>
```

### Angular Example

```typescript
// Component
export class ProfileScoreComponent {
  profileScore: any;
  isArabic: boolean = false;

  ngOnInit() {
    this.isArabic = this.translateService.currentLang === 'ar';
    this.loadProfileScore();
  }

  getScoreDetails() {
    return this.isArabic ? this.profileScore.details_ar : this.profileScore.details;
  }

  getImprovementTips() {
    return this.isArabic ? this.profileScore.improvement_tips_ar : this.profileScore.improvement_tips;
  }
}
```

```html
<!-- Template -->
<div class="score-container">
  <h3>{{ 'PROFILE.SCORE.TITLE' | translate }}</h3>
  
  <div class="score-breakdown">
    <div *ngFor="let detail of getScoreDetails() | keyvalue" class="score-item">
      <span class="label">{{ detail.key | translate }}</span>
      <span class="value">{{ detail.value }}</span>
    </div>
  </div>
  
  <div *ngIf="getImprovementTips().length > 0" class="improvement-tips">
    <h4>{{ 'PROFILE.SCORE.IMPROVEMENT' | translate }}</h4>
    <ul>
      <li *ngFor="let tip of getImprovementTips()">{{ tip }}</li>
    </ul>
  </div>
</div>
```

## Key Points for Frontend Developers

1. **Automatic Inclusion**: Arabic translations are automatically included in all score-related API responses
2. **Language Detection**: Use the `details_ar` and `improvement_tips_ar` fields when the user's language is Arabic
3. **Fallback**: Always fallback to English (`details` and `improvement_tips`) if Arabic is not available
4. **Consistent Structure**: The Arabic translations follow the same structure as English, just with translated text
5. **Real-time Updates**: Score translations update automatically when the user's profile changes

## Available Fields in Score Responses

- `details` / `details_ar` - Score breakdown explanations
- `improvement_tips` / `improvement_tips_ar` - Suggestions for improvement
- `total` - Overall score (same in both languages)
- Individual score components (account_tier, verification, etc.)

The frontend can now provide a fully bilingual experience for the score system! 🎉
