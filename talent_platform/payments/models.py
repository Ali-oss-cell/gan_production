from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.

class SubscriptionPlan(models.Model):
    """Model for subscription plans available on the platform"""
    PLAN_CHOICES = [
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('back_ground_jobs', 'Background Jobs'),
        ('bands', 'Bands'),
    ]
    
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, unique=True)
    features = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    duration_months = models.IntegerField(default=12)  # Default to yearly subscription
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']  # Order plans by price
    
    def __str__(self):
        return f"{self.name.title()} (${self.price})"
    
    def get_features_list(self):
        """Convert JSON features to a list if it's not already"""
        if isinstance(self.features, list):
            return self.features
        return []
    
    def is_for_talent(self):
        """Check if this plan is for talent users"""
        return self.name in ['silver', 'gold', 'platinum', 'bands']
    
    def is_for_background(self):
        """Check if this plan is for background users"""
        return self.name == 'back_ground_jobs'
    
    def get_account_type(self):
        """Get the corresponding account type for this plan"""
        if self.name == 'back_ground_jobs':
            return 'back_ground_jobs'
        return self.name  # For talent plans, account type matches plan name
    
    def get_monthly_price(self):
        """Calculate monthly price"""
        return self.price / self.duration_months
    
    def get_display_price(self):
        """Get formatted price string"""
        return f"${self.price}/year (${self.get_monthly_price():.2f}/month)"
    
    @classmethod
    def get_available_plans(cls, user_type):
        """Get available plans based on user type"""
        if user_type == 'talent':
            return cls.objects.filter(
                name__in=['silver', 'gold', 'platinum', 'bands'],
                is_active=True
            )
        elif user_type == 'background':
            return cls.objects.filter(
                name='back_ground_jobs',
                is_active=True
            )
        return cls.objects.none()

class Subscription(models.Model):
    """Model for user subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('trialing', 'Trialing'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    stripe_customer_id = models.CharField(max_length=100)
    stripe_subscription_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'plan', 'is_active']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    def is_valid(self):
        """Check if subscription is currently valid"""
        now = timezone.now()
        return (
            self.is_active and
            self.status == 'active' and
            (self.end_date is None or self.end_date > now)
        )
    
    def get_remaining_days(self):
        """Get remaining days in current period"""
        if not self.current_period_end:
            return 0
        remaining = self.current_period_end - timezone.now()
        return max(0, remaining.days)
    
    def get_next_billing_date(self):
        """Get next billing date"""
        return self.current_period_end
    
    def cancel(self):
        """Cancel the subscription"""
        self.cancel_at_period_end = True
        self.save()
    
    def reactivate(self):
        """Reactivate a canceled subscription"""
        self.cancel_at_period_end = False
        self.save()
    
    def update_status(self, new_status):
        """Update subscription status"""
        self.status = new_status
        if new_status == 'canceled':
            self.is_active = False
            self.end_date = timezone.now()
        self.save()
    
    def get_price_info(self):
        """Get price information for the subscription"""
        return {
            'plan_name': self.plan.name,
            'price': float(self.plan.price),
            'monthly_price': float(self.plan.get_monthly_price()),
            'duration_months': self.plan.duration_months,
            'display_price': self.plan.get_display_price()
        }

class PaymentTransaction(models.Model):
    """Model for payment transactions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('requires_payment_method', 'Requires Payment Method'),
        ('requires_confirmation', 'Requires Confirmation'),
        ('requires_action', 'Requires Action'),
        ('processing', 'Processing'),
        ('canceled', 'Canceled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True)
    stripe_charge_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='card')
    payment_method_details = models.JSONField(null=True, blank=True)
    billing_details = models.JSONField(null=True, blank=True)
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} - {self.status}"
    
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'completed'
    
    def is_refunded(self):
        """Check if payment was refunded"""
        return self.status == 'refunded'
    
    def get_payment_method_display(self):
        """Get formatted payment method details"""
        if not self.payment_method_details:
            return self.get_payment_method_display()
        
        if self.payment_method == 'card':
            card = self.payment_method_details.get('card', {})
            return f"Card ending in {card.get('last4', '****')}"
        return self.get_payment_method_display()
    
    def get_billing_details_display(self):
        """Get formatted billing details"""
        if not self.billing_details:
            return "No billing details"
        
        address = self.billing_details.get('address', {})
        return f"{self.billing_details.get('name', '')}, {address.get('line1', '')}, {address.get('city', '')}, {address.get('country', '')}"
    
    def get_amount_display(self):
        """Get formatted amount with currency"""
        return f"{self.currency} {self.amount}"
    
    def get_refunded_amount_display(self):
        """Get formatted refunded amount with currency"""
        return f"{self.currency} {self.refunded_amount}"
    
    def get_net_amount(self):
        """Get net amount after refunds"""
        return self.amount - self.refunded_amount

