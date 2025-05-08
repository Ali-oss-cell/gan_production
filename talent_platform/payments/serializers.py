from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, PaymentTransaction
from .pricing_config import SUBSCRIPTION_PLANS

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()
    monthly_equivalent = serializers.SerializerMethodField()
    stripe_price_id = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'price',
            'features',
            'duration_months',
            'stripe_price_id',
            'monthly_equivalent',
            'is_active'
        ]

    def get_features(self, obj):
        # Get features from pricing config
        plan_config = SUBSCRIPTION_PLANS.get(obj.name.upper())
        return plan_config['features'] if plan_config else []

    def get_monthly_equivalent(self, obj):
        # Calculate monthly price
        return str(float(obj.price) / obj.duration_months)

    def get_stripe_price_id(self, obj):
        # Get Stripe price ID from config
        plan_config = SUBSCRIPTION_PLANS.get(obj.name.upper())
        return plan_config['stripe_price_id'] if plan_config else None

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_price = serializers.DecimalField(source='plan.price', read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'plan_name', 'plan_price', 'status', 
                  'start_date', 'end_date', 'is_active']
        read_only_fields = ['stripe_customer_id', 'stripe_subscription_id', 'status', 
                            'start_date', 'end_date']

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

class CreatePaymentIntentSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)  # Amount in cents
    currency = serializers.CharField(default='usd')
    payment_method_types = serializers.ListField(
        child=serializers.CharField(), 
        default=['card']
    ) 