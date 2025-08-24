import stripe
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import PaymentTransaction, PaymentMethodSupport, Subscription
from .payment_methods_config import get_payment_method_config, is_payment_method_supported

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentMethodService:
    """Service for handling payment methods"""
    
    @staticmethod
    def get_available_methods(user, amount=None, currency='USD'):
        """Get available payment methods for a user based on their region"""
        # Get user's region (you might need to implement this based on your user model)
        region = getattr(user, 'country', 'us').lower()
        
        # Get supported methods from database
        available_methods = PaymentMethodSupport.get_available_methods(
            region, currency, amount
        )
        
        # Filter by amount limits
        if amount:
            filtered_methods = []
            for method in available_methods:
                config = get_payment_method_config(method)
                if config:
                    min_amount = config.get('min_amount', Decimal('0'))
                    max_amount = config.get('max_amount', Decimal('999999.99'))
                    if min_amount <= amount <= max_amount:
                        filtered_methods.append(method)
            return filtered_methods
        
        return list(available_methods)
    
    @staticmethod
    def create_payment_intent(user, amount, currency='USD', payment_method='card', metadata=None):
        """Create a Stripe payment intent"""
        try:
            # Get payment method configuration
            config = get_payment_method_config(payment_method)
            if not config:
                raise ValueError(f"Unsupported payment method: {payment_method}")
            
            # Check if payment method is supported in user's region
            region = getattr(user, 'country', 'us').lower()
            if not is_payment_method_supported(payment_method, region):
                raise ValueError(f"Payment method {payment_method} not supported in {region}")
            
            # Calculate fees
            processing_fee = config.get('processing_fee', Decimal('0'))
            fixed_fee = config.get('fixed_fee', Decimal('0'))
            total_fee = (amount * processing_fee / 100) + fixed_fee
            total_amount = amount + total_fee
            
            # Create payment intent
            intent_data = {
                'amount': int(total_amount * 100),  # Convert to cents
                'currency': currency.lower(),
                'payment_method_types': [config['stripe_type']],
                'metadata': {
                    'user_id': str(user.id),
                    'payment_method': payment_method,
                    'processing_fee': str(total_fee),
                    **(metadata or {})
                }
            }
            
            # Add specific payment method data
            if payment_method in ['apple_pay', 'google_pay']:
                intent_data['payment_method_options'] = {
                    'card': {
                        'request_three_d_secure': 'automatic'
                    }
                }
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': total_amount,
                'processing_fee': total_fee,
                'currency': currency
            }
            
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Payment intent creation failed: {str(e)}")
    
    @staticmethod
    def confirm_payment(payment_intent_id, payment_method_id=None):
        """Confirm a payment intent"""
        try:
            if payment_method_id:
                stripe.PaymentIntent.confirm(
                    payment_intent_id,
                    payment_method=payment_method_id
                )
            else:
                stripe.PaymentIntent.confirm(payment_intent_id)
            
            return True
        except stripe.error.StripeError as e:
            raise ValueError(f"Payment confirmation failed: {str(e)}")
    
    @staticmethod
    def create_payment_transaction(user, payment_intent_id, amount, payment_method, subscription=None):
        """Create a payment transaction record"""
        try:
            # Get payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Create transaction record
            transaction = PaymentTransaction.objects.create(
                user=user,
                subscription=subscription,
                amount=amount,
                currency=payment_intent.currency.upper(),
                stripe_payment_intent_id=payment_intent_id,
                stripe_charge_id=payment_intent.latest_charge,
                status=payment_intent.status,
                payment_method=payment_method,
                payment_method_details=payment_intent.payment_method_data if hasattr(payment_intent, 'payment_method_data') else None,
                billing_details=payment_intent.charges.data[0].billing_details if payment_intent.charges.data else None
            )
            
            return transaction
            
        except Exception as e:
            raise ValueError(f"Transaction creation failed: {str(e)}")
    
    @staticmethod
    def get_payment_method_details(payment_method_id):
        """Get details of a payment method"""
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            return payment_method
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to retrieve payment method: {str(e)}")
    
    @staticmethod
    def attach_payment_method_to_customer(payment_method_id, customer_id):
        """Attach a payment method to a customer"""
        try:
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            return True
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to attach payment method: {str(e)}")
    
    @staticmethod
    def detach_payment_method(payment_method_id):
        """Detach a payment method from a customer"""
        try:
            stripe.PaymentMethod.detach(payment_method_id)
            return True
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to detach payment method: {str(e)}")

class ApplePayService:
    """Service for Apple Pay specific functionality"""
    
    @staticmethod
    def create_domain_verification_file():
        """Create Apple Pay domain verification file"""
        # This should create a file at .well-known/apple-developer-merchantid-domain-association
        # You'll need to get the actual content from Apple
        verification_content = """
        # Apple Pay Domain Verification File
        # This file should be placed at: .well-known/apple-developer-merchantid-domain-association
        # Get the actual content from Apple Developer Portal
        """
        return verification_content
    
    @staticmethod
    def validate_apple_pay_session(domain, validation_url):
        """Validate Apple Pay session"""
        try:
            # This is a simplified version - you'll need to implement the actual validation
            # according to Apple's documentation
            return True
        except Exception as e:
            raise ValueError(f"Apple Pay validation failed: {str(e)}")

class GooglePayService:
    """Service for Google Pay specific functionality"""
    
    @staticmethod
    def get_google_pay_configuration():
        """Get Google Pay configuration for frontend"""
        return {
            'environment': 'TEST' if settings.DEBUG else 'PRODUCTION',
            'merchantInfo': {
                'merchantName': getattr(settings, 'STRIPE_MERCHANT_NAME', 'Gan7Club'),
                'merchantId': getattr(settings, 'STRIPE_MERCHANT_ID', ''),
            },
            'allowedPaymentMethods': [{
                'type': 'CARD',
                'parameters': {
                    'allowedAuthMethods': ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
                    'allowedCardNetworks': ['VISA', 'MASTERCARD', 'AMEX'],
                },
                'tokenizationSpecification': {
                    'type': 'PAYMENT_GATEWAY',
                    'parameters': {
                        'gateway': 'stripe',
                        'gatewayMerchantId': getattr(settings, 'STRIPE_MERCHANT_ID', ''),
                    },
                },
            }],
            'transactionInfo': {
                'totalPriceStatus': 'FINAL',
                'totalPriceLabel': 'Total',
                'currencyCode': 'USD',
                'countryCode': 'US',
            },
        } 

class StripePaymentService:
    """Service for handling Stripe payments and webhooks"""
    
    @staticmethod
    def create_subscription_checkout_session(user, plan, success_url, cancel_url, region_code='us'):
        """Create a Stripe checkout session for subscription"""
        try:
            # Get or create Stripe customer
            customer = StripePaymentService.get_or_create_customer(user)
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                    'plan_name': plan.name
                }
            )
            
            return session
            
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to create checkout session: {str(e)}")
    
    @staticmethod
    def get_or_create_customer(user):
        """Get or create a Stripe customer for the user"""
        try:
            # Check if user already has a Stripe customer ID
            if hasattr(user, 'stripe_customer_id') and user.stripe_customer_id:
                return stripe.Customer.retrieve(user.stripe_customer_id)
            
            # Create new customer
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}" if hasattr(user, 'first_name') else user.email,
                metadata={
                    'user_id': str(user.id),
                    'platform': 'gan7club'
                }
            )
            
            # Save customer ID to user model
            user.stripe_customer_id = customer.id
            user.save(update_fields=['stripe_customer_id'])
            
            return customer
            
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to get/create customer: {str(e)}")
    
    @staticmethod
    def handle_webhook_event(payload, sig_header):
        """Handle Stripe webhook events"""
        try:
            print(f"🔄 Processing webhook event...")
            
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            print(f"   Event type: {event['type']}")
            print(f"   Event ID: {event.get('id', 'unknown')}")
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                print("   Handling checkout.session.completed")
                StripePaymentService.handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'customer.subscription.created':
                print("   Handling customer.subscription.created")
                StripePaymentService.handle_subscription_created(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                print("   Handling customer.subscription.updated")
                StripePaymentService.handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                print("   Handling customer.subscription.deleted")
                StripePaymentService.handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                print("   Handling invoice.payment_succeeded")
                StripePaymentService.handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                print("   Handling invoice.payment_failed")
                StripePaymentService.handle_payment_failed(event['data']['object'])
            else:
                print(f"   ⚠️  Unhandled event type: {event['type']}")
            
            print(f"✅ Webhook event {event['type']} processed successfully")
            return True
            
        except ValueError as e:
            print(f"❌ Webhook signature verification failed: {str(e)}")
            raise e
        except Exception as e:
            print(f"❌ Webhook handling failed: {str(e)}")
            raise ValueError(f"Webhook handling failed: {str(e)}")
    
    @staticmethod
    def handle_checkout_completed(session):
        """Handle checkout.session.completed event"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get user from session metadata
            user_id = session.metadata.get('user_id')
            if not user_id:
                raise ValueError("No user_id in session metadata")
            
            user = User.objects.get(id=user_id)
            
            # Get subscription from Stripe
            subscription = stripe.Subscription.retrieve(session.subscription)
            
            # Create or update subscription in database
            StripePaymentService.create_or_update_subscription(user, subscription)
            
        except Exception as e:
            raise ValueError(f"Failed to handle checkout completed: {str(e)}")
    
    @staticmethod
    def handle_subscription_created(subscription_data):
        """Handle customer.subscription.created event"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get customer
            customer = stripe.Customer.retrieve(subscription_data.customer)
            
            # Find user by Stripe customer ID
            try:
                user = User.objects.get(stripe_customer_id=customer.id)
            except User.DoesNotExist:
                # Try to find by email
                user = User.objects.get(email=customer.email)
                # Update user with Stripe customer ID
                user.stripe_customer_id = customer.id
                user.save(update_fields=['stripe_customer_id'])
            
            # Create or update subscription
            StripePaymentService.create_or_update_subscription(user, subscription_data)
            
        except Exception as e:
            raise ValueError(f"Failed to handle subscription created: {str(e)}")
    
    @staticmethod
    def handle_subscription_updated(subscription_data):
        """Handle customer.subscription.updated event"""
        try:
            # Find existing subscription
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_data.id
            )
            
            # Update subscription data
            StripePaymentService.update_subscription_from_stripe(subscription, subscription_data)
            
        except Subscription.DoesNotExist:
            # If subscription doesn't exist, create it
            StripePaymentService.handle_subscription_created(subscription_data)
        except Exception as e:
            raise ValueError(f"Failed to handle subscription updated: {str(e)}")
    
    @staticmethod
    def handle_subscription_deleted(subscription_data):
        """Handle customer.subscription.deleted event"""
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_data.id
            )
            
            # Mark subscription as canceled
            subscription.status = 'canceled'
            subscription.is_active = False
            subscription.end_date = timezone.now()
            subscription.save()
            
        except Subscription.DoesNotExist:
            pass  # Subscription already deleted
        except Exception as e:
            raise ValueError(f"Failed to handle subscription deleted: {str(e)}")
    
    @staticmethod
    def handle_payment_succeeded(invoice_data):
        """Handle invoice.payment_succeeded event"""
        try:
            print(f"🔄 Processing payment succeeded for invoice: {invoice_data.id}")
            print(f"   Subscription ID: {invoice_data.subscription}")
            
            # Find subscription and update status to active
            subscription = Subscription.objects.get(
                stripe_subscription_id=invoice_data.subscription
            )
            
            print(f"   Found subscription {subscription.id} for user {subscription.user.id}")
            print(f"   Plan: {subscription.plan.name}")
            print(f"   Previous status: {subscription.status}, is_active: {subscription.is_active}")
            
            # Update subscription status to active
            subscription.status = 'active'
            subscription.is_active = True
            subscription.save()
            
            print(f"✅ Payment succeeded for invoice: {invoice_data.id}, subscription {subscription.id} activated")
            print(f"   New status: {subscription.status}, is_active: {subscription.is_active}")
            
        except Subscription.DoesNotExist:
            print(f"❌ Payment succeeded for invoice: {invoice_data.id}, but subscription not found")
            print(f"   Looking for subscription ID: {invoice_data.subscription}")
        except Exception as e:
            print(f"❌ Error in handle_payment_succeeded: {str(e)}")
            raise ValueError(f"Failed to handle payment succeeded: {str(e)}")
    
    @staticmethod
    def handle_payment_failed(invoice_data):
        """Handle invoice.payment_failed event"""
        try:
            # Find subscription and update status
            subscription = Subscription.objects.get(
                stripe_subscription_id=invoice_data.subscription
            )
            
            subscription.status = 'past_due'
            subscription.save()
            
        except Subscription.DoesNotExist:
            pass
        except Exception as e:
            raise ValueError(f"Failed to handle payment failed: {str(e)}")
    
    @staticmethod
    def create_or_update_subscription(user, stripe_subscription):
        """Create or update subscription in database"""
        try:
            from .models import SubscriptionPlan
            
            # Get the plan from Stripe price ID
            # Handle Stripe subscription items - items is a method that returns a list object
            try:
                # Call items() method to get the list
                items_list = stripe_subscription.items()
                if hasattr(items_list, 'data') and items_list.data:
                    price_id = items_list.data[0].price.id
                elif hasattr(items_list, '__iter__') and len(items_list) > 0:
                    # Sometimes it's directly iterable
                    price_id = items_list[0].price.id
                else:
                    raise ValueError(f"No items found in subscription items: {items_list}")
            except Exception as e:
                # Fallback: try as attribute (older Stripe versions)
                try:
                    if hasattr(stripe_subscription.items, 'data') and stripe_subscription.items.data:
                        price_id = stripe_subscription.items.data[0].price.id
                    else:
                        raise ValueError(f"Could not extract price ID from subscription items. Items type: {type(stripe_subscription.items)}, Error: {e}")
                except Exception as fallback_error:
                    raise ValueError(f"Could not extract price ID from subscription items. Original error: {e}, Fallback error: {fallback_error}")
            
            print(f"   Looking for plan with price_id: {price_id}")
            plan = SubscriptionPlan.objects.get(stripe_price_id=price_id)
            print(f"   Found plan: {plan.name} (ID: {plan.id})")
            
            # Create or update subscription
            subscription, created = Subscription.objects.update_or_create(
                stripe_subscription_id=stripe_subscription.id,
                defaults={
                    'user': user,
                    'plan': plan,
                    'stripe_customer_id': stripe_subscription.customer,
                    'status': stripe_subscription.status,
                    'current_period_start': timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_start, tz=timezone.utc
                    ),
                    'current_period_end': timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_end, tz=timezone.utc
                    ),
                    'cancel_at_period_end': stripe_subscription.cancel_at_period_end,
                    # For new subscriptions, set is_active based on whether payment succeeded
                    # 'incomplete' means waiting for payment, 'active' means payment succeeded
                    'is_active': stripe_subscription.status in ['active', 'trialing']
                }
            )
            
            return subscription
            
        except Exception as e:
            raise ValueError(f"Failed to create/update subscription: {str(e)}")
    
    @staticmethod
    def update_subscription_from_stripe(subscription, stripe_subscription):
        """Update subscription with data from Stripe"""
        try:
            subscription.status = stripe_subscription.status
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_start, tz=timezone.utc
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_end, tz=timezone.utc
            )
            subscription.cancel_at_period_end = stripe_subscription.cancel_at_period_end
            subscription.is_active = stripe_subscription.status == 'active'
            
            if stripe_subscription.status == 'canceled':
                subscription.end_date = timezone.now()
            
            subscription.save()
            
            return subscription
            
        except Exception as e:
            raise ValueError(f"Failed to update subscription: {str(e)}")
    
    @staticmethod
    def cancel_subscription(subscription):
        """Cancel a subscription in Stripe"""
        try:
            # Cancel in Stripe
            stripe_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            # Update local subscription
            subscription.cancel_at_period_end = True
            subscription.save()
            
            return True
            
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to cancel subscription: {str(e)}")
    
    @staticmethod
    def get_subscription_status(subscription):
        """Get current subscription status from Stripe"""
        try:
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            return {
                'status': stripe_sub.status,
                'current_period_end': timezone.datetime.fromtimestamp(
                    stripe_sub.current_period_end, tz=timezone.utc
                ).isoformat(),
                'cancel_at_period_end': stripe_sub.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to get subscription status: {str(e)}")
    
    @staticmethod
    def get_payment_methods_for_region(region_code):
        """Get available payment methods for a region"""
        # This is a simplified version - you can expand based on your needs
        base_methods = ['card']
        
        if region_code.lower() in ['us', 'ca']:
            return base_methods + ['apple_pay', 'google_pay']
        elif region_code.lower() in ['eu']:
            return base_methods + ['sepa_debit', 'ideal', 'sofort']
        elif region_code.lower() in ['gb']:
            return base_methods + ['bacs_debit']
        else:
            return base_methods 