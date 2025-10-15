# Plan Translations API Examples

## How Frontend Gets Arabic Plan Translations

The Arabic translations for subscription plans are automatically included in all API responses. Here are the key API endpoints and their responses:

## 1. Subscription Plans API

### Endpoint: `GET /api/payments/plans/`

**Response Example:**
```json
{
  "results": [
    {
      "id": 1,
      "name": "Premium",
      "name_ar": "بريميوم",
      "description_ar": "خطة احترافية للمواهب الطموحة",
      "price": "99.99",
      "features": [
        "Upload up to 4 profile pictures",
        "Upload up to 2 showcase videos",
        "Enhanced search visibility (50% boost)",
        "Profile verification badge"
      ],
      "features_ar": [
        "رفع حتى 4 صور للملف الشخصي",
        "رفع حتى فيديوين للعرض",
        "ظهور محسن في البحث (زيادة 50%)",
        "شارة تحقق للملف الشخصي"
      ],
      "duration_months": 12,
      "stripe_price_id": "price_premium",
      "monthly_equivalent": "8.33",
      "is_active": true
    },
    {
      "id": 2,
      "name": "Platinum",
      "name_ar": "بلاتينيوم",
      "description_ar": "خطة متقدمة مع مميزات حصرية",
      "price": "199.99",
      "features": [
        "Upload up to 6 profile pictures",
        "Upload up to 4 showcase videos",
        "Highest search visibility (100% boost)",
        "Profile verification badge",
        "Featured profile placement"
      ],
      "features_ar": [
        "رفع حتى 6 صور للملف الشخصي",
        "رفع حتى 4 فيديوهات للعرض",
        "أعلى ظهور في البحث (زيادة 100%)",
        "شارة تحقق للملف الشخصي",
        "وضع مميز للملف الشخصي"
      ],
      "duration_months": 12,
      "stripe_price_id": "price_platinum",
      "monthly_equivalent": "16.67",
      "is_active": true
    },
    {
      "id": 3,
      "name": "Background Jobs Professional",
      "name_ar": "وظائف الخلفية المحترفة",
      "description_ar": "خطة مخصصة لمحترفي وظائف الخلفية",
      "price": "249.99",
      "features": [
        "Create and manage props",
        "Create and manage costumes",
        "Create and manage locations",
        "Create and manage memorabilia",
        "Create and manage vehicles",
        "Create and manage artistic materials",
        "Create and manage music items",
        "Create and manage rare items",
        "Rent and sell items",
        "Share items with other users"
      ],
      "features_ar": [
        "إنشاء وإدارة الدعائم",
        "إنشاء وإدارة الأزياء",
        "إنشاء وإدارة المواقع",
        "إنشاء وإدارة التذكارات",
        "إنشاء وإدارة المركبات",
        "إنشاء وإدارة المواد الفنية",
        "إنشاء وإدارة العناصر الموسيقية",
        "إنشاء وإدارة العناصر النادرة",
        "تأجير وبيع العناصر",
        "مشاركة العناصر مع المستخدمين الآخرين"
      ],
      "duration_months": 12,
      "stripe_price_id": "price_background",
      "monthly_equivalent": "20.83",
      "is_active": true
    },
    {
      "id": 4,
      "name": "Bands",
      "name_ar": "الفرق الموسيقية",
      "description_ar": "خطة مخصصة للفرق الموسيقية والمسرحية",
      "price": "149.99",
      "features": [
        "Create and manage bands",
        "Unlimited member invitations",
        "Band media uploads (5 images, 5 videos)",
        "Band management tools"
      ],
      "features_ar": [
        "إنشاء وإدارة الفرق",
        "دعوات غير محدودة للأعضاء",
        "رفع وسائط الفرقة (5 صور، 5 فيديوهات)",
        "أدوات إدارة الفرقة"
      ],
      "duration_months": 12,
      "stripe_price_id": "price_bands",
      "monthly_equivalent": "12.50",
      "is_active": true
    }
  ]
}
```

## 2. User Subscriptions API

### Endpoint: `GET /api/payments/subscriptions/`

**Response Example:**
```json
{
  "results": [
    {
      "id": 123,
      "plan": 1,
      "plan_name": "Premium",
      "plan_name_ar": "بريميوم",
      "plan_price": "99.99",
      "status": "active",
      "status_ar": "نشط",
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2025-01-01T00:00:00Z",
      "is_active": true,
      "current_period_end": "2025-01-01T00:00:00Z"
    }
  ]
}
```

## 3. Payment Transactions API

### Endpoint: `GET /api/payments/transactions/`

**Response Example:**
```json
{
  "results": [
    {
      "id": 456,
      "subscription": 123,
      "amount": 9999,
      "currency": "usd",
      "status": "succeeded",
      "status_ar": "نجح",
      "payment_method": "card",
      "payment_method_ar": "بطاقة ائتمان",
      "created_at": "2024-01-01T10:30:00Z"
    }
  ]
}
```

## Frontend Implementation Examples

### React/JavaScript Example

```javascript
// Get subscription plans
const response = await fetch('/api/payments/plans/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const plansData = await response.json();
const plans = plansData.results;

// Use Arabic translations based on user language preference
const userLanguage = localStorage.getItem('language') || 'en';
const isArabic = userLanguage === 'ar';

// Display plan information
plans.forEach(plan => {
  const planName = isArabic ? plan.name_ar : plan.name;
  const planDescription = isArabic ? plan.description_ar : plan.description;
  const planFeatures = isArabic ? plan.features_ar : plan.features;
  
  console.log(`Plan: ${planName}`);
  console.log(`Description: ${planDescription}`);
  console.log(`Features: ${planFeatures.join(', ')}`);
});
```

### Vue.js Example

```vue
<template>
  <div class="plans-container">
    <div v-for="plan in plans" :key="plan.id" class="plan-card">
      <h3>{{ getPlanName(plan) }}</h3>
      <p class="description">{{ getPlanDescription(plan) }}</p>
      <div class="price">${{ plan.price }}</div>
      <ul class="features">
        <li v-for="feature in getPlanFeatures(plan)" :key="feature">
          {{ feature }}
        </li>
      </ul>
      <button @click="subscribe(plan.id)">
        {{ $t('plans.subscribe') }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      plans: []
    }
  },
  computed: {
    isArabic() {
      return this.$i18n.locale === 'ar';
    }
  },
  methods: {
    getPlanName(plan) {
      return this.isArabic ? plan.name_ar : plan.name;
    },
    getPlanDescription(plan) {
      return this.isArabic ? plan.description_ar : plan.description;
    },
    getPlanFeatures(plan) {
      return this.isArabic ? plan.features_ar : plan.features;
    },
    async loadPlans() {
      const response = await fetch('/api/payments/plans/');
      const data = await response.json();
      this.plans = data.results;
    }
  },
  mounted() {
    this.loadPlans();
  }
}
</script>
```

### Angular Example

```typescript
// Component
export class PlansComponent {
  plans: any[] = [];
  isArabic: boolean = false;

  ngOnInit() {
    this.isArabic = this.translateService.currentLang === 'ar';
    this.loadPlans();
  }

  getPlanName(plan: any): string {
    return this.isArabic ? plan.name_ar : plan.name;
  }

  getPlanDescription(plan: any): string {
    return this.isArabic ? plan.description_ar : plan.description;
  }

  getPlanFeatures(plan: any): string[] {
    return this.isArabic ? plan.features_ar : plan.features;
  }

  async loadPlans() {
    const response = await fetch('/api/payments/plans/');
    const data = await response.json();
    this.plans = data.results;
  }
}
```

```html
<!-- Template -->
<div class="plans-grid">
  <div *ngFor="let plan of plans" class="plan-card">
    <h3>{{ getPlanName(plan) }}</h3>
    <p class="description">{{ getPlanDescription(plan) }}</p>
    <div class="price">${{ plan.price }}</div>
    <ul class="features">
      <li *ngFor="let feature of getPlanFeatures(plan)">
        {{ feature }}
      </li>
    </ul>
    <button (click)="subscribe(plan.id)">
      {{ 'PLANS.SUBSCRIBE' | translate }}
    </button>
  </div>
</div>
```

## Subscription Status Display

### React Example for Subscription Status

```javascript
// Display subscription status
const subscription = userSubscriptions[0];
const statusText = isArabic ? subscription.status_ar : subscription.status;
const planName = isArabic ? subscription.plan_name_ar : subscription.plan_name;

console.log(`Your ${planName} subscription is ${statusText}`);
// Arabic: "اشتراكك في بريميوم نشط"
// English: "Your Premium subscription is active"
```

## Payment History Display

### Vue.js Example for Payment History

```vue
<template>
  <div class="payment-history">
    <h3>{{ $t('payments.history') }}</h3>
    <div v-for="transaction in transactions" :key="transaction.id" class="transaction">
      <div class="amount">${{ transaction.amount / 100 }}</div>
      <div class="status">{{ getStatusText(transaction) }}</div>
      <div class="method">{{ getPaymentMethod(transaction) }}</div>
      <div class="date">{{ formatDate(transaction.created_at) }}</div>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    getStatusText(transaction) {
      return this.isArabic ? transaction.status_ar : transaction.status;
    },
    getPaymentMethod(transaction) {
      return this.isArabic ? transaction.payment_method_ar : transaction.payment_method;
    }
  }
}
</script>
```

## Key Points for Frontend Developers

1. **Automatic Inclusion**: Arabic translations are automatically included in all plan-related API responses
2. **Language Detection**: Use the `_ar` fields when the user's language is Arabic
3. **Fallback**: Always fallback to English fields if Arabic is not available
4. **Consistent Structure**: The Arabic translations follow the same structure as English
5. **Real-time Updates**: Plan translations update automatically when plans change

## Available Fields in Plan Responses

- `name` / `name_ar` - Plan names
- `description_ar` - Plan descriptions (Arabic only)
- `features` / `features_ar` - Plan features lists
- `status` / `status_ar` - Subscription status
- `payment_method` / `payment_method_ar` - Payment methods

The frontend can now provide a fully bilingual experience for the subscription plans system! 🎉
