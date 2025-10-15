from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, PaymentTransaction
from .pricing_config import SUBSCRIPTION_PLANS
from datetime import datetime, timedelta

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()
    monthly_equivalent = serializers.SerializerMethodField()
    stripe_price_id = serializers.SerializerMethodField()
    # Arabic translations
    name_ar = serializers.SerializerMethodField()
    description_ar = serializers.SerializerMethodField()
    features_ar = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'name_ar',
            'description_ar',
            'price',
            'features',
            'features_ar',
            'duration_months',
            'stripe_price_id',
            'monthly_equivalent',
            'is_active'
        ]

    def get_features(self, obj):
        # Get features from pricing config
        plan_key = obj.name.upper()
        # Handle special case for background_jobs
        if obj.name == 'background_jobs':
            plan_key = 'BACKGROUND_JOBS'
        plan_config = SUBSCRIPTION_PLANS.get(plan_key)
        return plan_config['features'] if plan_config else []

    def get_monthly_equivalent(self, obj):
        # Calculate monthly price
        return str(float(obj.price) / obj.duration_months)

    def get_stripe_price_id(self, obj):
        # Get Stripe price ID from config
        plan_key = obj.name.upper()
        # Handle special case for background_jobs
        if obj.name == 'background_jobs':
            plan_key = 'BACKGROUND_JOBS'
        plan_config = SUBSCRIPTION_PLANS.get(plan_key)
        return plan_config['stripe_price_id'] if plan_config else None

    def get_name_ar(self, obj):
        """Return Arabic name for the plan"""
        name_translations = {
            'premium': 'بريميوم',
            'platinum': 'بلاتينيوم',
            'background_jobs': 'وظائف الخلفية المحترفة',
            'bands': 'الفرق الموسيقية',
        }
        return name_translations.get(obj.name, obj.name)

    def get_description_ar(self, obj):
        """Return Arabic description for the plan"""
        description_translations = {
            'premium': 'خطة احترافية للمواهب الطموحة',
            'platinum': 'خطة متقدمة مع مميزات حصرية',
            'background_jobs': 'خطة مخصصة لمحترفي وظائف الخلفية',
            'bands': 'خطة مخصصة للفرق الموسيقية والمسرحية',
        }
        return description_translations.get(obj.name, obj.description or '')

    def get_features_ar(self, obj):
        """Return Arabic features list"""
        features_translations = {
            'premium': [
                'ملف احترافي مع عرض أعمالك',
                'ظهور قوي في نتائج البحث',
                'اتصال مباشر مع شركات الإنتاج',
                'إمكانية رفع ملفات الوسائط',
                'دعم مميز وطلبات حجز فورية'
            ],
            'platinum': [
                'جميع مميزات البريميوم',
                'أولوية قصوى في نتائج البحث',
                'شارة تحقق مميزة',
                'تحليلات متقدمة للملف الشخصي',
                'دعم VIP على مدار الساعة',
                'إمكانية إنشاء محفظة أعمال موسعة'
            ],
            'background_jobs': [
                'ملف احترافي للوظائف الخلفية',
                'ظهور في بحث الوظائف الخلفية',
                'رفع السيرة الذاتية والشهادات',
                'تنبيهات فورية للوظائف الجديدة',
                'اتصال مباشر مع أصحاب العمل'
            ],
            'bands': [
                'صفحة مخصصة للفرقة',
                'إدارة الأعضاء وتنظيم الأدوار',
                'جدول الفعاليات والحجوزات',
                'عرض وسائط الفرقة (صور وفيديو)',
                'أفضلية في طلبات الحجز من المنظمين',
                'دعم مخصص لاحتياجات المجموعة'
            ]
        }
        return features_translations.get(obj.name, [])

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_price = serializers.DecimalField(source='plan.price', read_only=True, max_digits=10, decimal_places=2)
    end_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'plan_name', 'plan_price', 'status', 
                  'start_date', 'end_date', 'is_active', 'current_period_end']
        read_only_fields = ['stripe_customer_id', 'stripe_subscription_id', 'status', 
                            'start_date', 'current_period_end']

    def get_end_date(self, obj):
        """
        Calculate the end date for the subscription.
        For recurring subscriptions, use current_period_end.
        For fixed-term subscriptions, use the end_date field.
        """
        try:
            # If there's a current_period_end (recurring subscription), use that
            if obj.current_period_end:
                return obj.current_period_end.isoformat()
            
            # If there's a fixed end_date, use that
            if obj.end_date:
                return obj.end_date.isoformat()
            
            # If neither exists, calculate from start_date and plan duration (approximate)
            if obj.start_date and obj.plan.duration_months:
                # Approximate months as 30 days each
                days_to_add = obj.plan.duration_months * 30
                calculated_end = obj.start_date + timedelta(days=days_to_add)
                return calculated_end.isoformat()
            
            # If we can't calculate, return None
            return None
            
        except Exception as e:
            print(f"Error calculating end_date for subscription {obj.id}: {e}")
            return None

class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ['id', 'subscription', 'amount', 'currency', 'status', 
                  'payment_method', 'created_at']
        read_only_fields = ['stripe_payment_intent_id', 'status', 'created_at', 'updated_at']

class CreateCheckoutSessionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()
    region_code = serializers.CharField(required=False, default='ae')  # Default to UAE

class CreatePaymentIntentSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)  # Amount in cents
    currency = serializers.CharField(default='usd')
    payment_method_types = serializers.ListField(
        child=serializers.CharField(), 
        default=['card']
    ) 