from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, PaymentTransaction

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'description', 'price', 'features', 'is_active']

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