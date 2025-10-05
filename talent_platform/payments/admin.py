from django.contrib import admin
from .models_restrictions import RestrictedCountryUser
from .models import SubscriptionPlan, Subscription, PaymentTransaction

@admin.register(RestrictedCountryUser)
class RestrictedCountryUserAdmin(admin.ModelAdmin):
    """
    Admin interface for managing users from restricted countries.
    Integrates with existing dashboard functionality.
    """
    list_display = [
        'user_email', 
        'country', 
        'is_approved', 
        'account_type', 
        'created_at', 
        'last_updated_by'
    ]
    list_filter = [
        'is_approved', 
        'account_type', 
        'country', 
        'created_at'
    ]
    search_fields = [
        'user__email', 
        'user__first_name', 
        'user__last_name', 
        'country', 
        'notes'
    ]
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_users', 'reject_users', 'upgrade_to_premium', 'upgrade_to_platinum', 'downgrade_to_free']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'country', 'account_type')
        }),
        ('Approval Status', {
            'fields': ('is_approved', 'last_updated_by')
        }),
        ('Notes & Tracking', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Display user email in list view"""
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def approve_users(self, request, queryset):
        """Approve selected restricted country users"""
        updated = queryset.update(
            is_approved=True, 
            last_updated_by=request.user
        )
        self.message_user(
            request, 
            f'Successfully approved {updated} restricted country user(s).'
        )
    approve_users.short_description = "Approve selected users"
    
    def reject_users(self, request, queryset):
        """Reject selected restricted country users"""
        updated = queryset.update(
            is_approved=False, 
            last_updated_by=request.user
        )
        self.message_user(
            request, 
            f'Successfully rejected {updated} restricted country user(s).'
        )
    reject_users.short_description = "Reject selected users"
    
    def upgrade_to_premium(self, request, queryset):
        """Upgrade selected users to premium account types"""
        for obj in queryset:
            if hasattr(obj.user, 'talent_user'):
                obj.user.talent_user.account_type = 'premium'
                obj.user.talent_user.save()
                obj.account_type = 'premium'
                obj.last_updated_by = request.user
                obj.save()
        
        self.message_user(
            request, 
            f'Successfully upgraded {queryset.count()} user(s) to premium.'
        )
    upgrade_to_premium.short_description = "Upgrade to premium"
    
    def upgrade_to_platinum(self, request, queryset):
        """Upgrade selected users to platinum account types"""
        for obj in queryset:
            if hasattr(obj.user, 'talent_user'):
                obj.user.talent_user.account_type = 'platinum'
                obj.user.talent_user.save()
                obj.account_type = 'platinum'
                obj.last_updated_by = request.user
                obj.save()
        
        self.message_user(
            request, 
            f'Successfully upgraded {queryset.count()} user(s) to platinum.'
        )
    upgrade_to_platinum.short_description = "Upgrade to platinum"
    
    def downgrade_to_free(self, request, queryset):
        """Downgrade selected users to free account types"""
        for obj in queryset:
            if hasattr(obj.user, 'talent_user'):
                obj.user.talent_user.account_type = 'free'
                obj.user.talent_user.save()
                obj.account_type = 'free'
                obj.last_updated_by = request.user
                obj.save()
        
        self.message_user(
            request, 
            f'Successfully downgraded {queryset.count()} user(s) to free.'
        )
    downgrade_to_free.short_description = "Downgrade to free"
    
    def get_queryset(self, request):
        """Custom queryset with user information"""
        return super().get_queryset(request).select_related('user', 'last_updated_by')

# Register existing models if not already registered
admin.site.register(SubscriptionPlan)
admin.site.register(Subscription)
admin.site.register(PaymentTransaction)
