import stripe
from django.conf import settings
from django.utils import timezone
from .models import SubscriptionPlan, Subscription, PaymentTransaction
from profiles.models import TalentUserProfile, BackGroundJobsProfile
from users.models import BaseUser
from .payment_methods_config import PAYMENT_METHODS_CONFIG, REGIONAL_PREFERENCES
from django.utils.timezone import datetime as dj_timezone
import pytz as py_timezone

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripePaymentService:
    @staticmethod
    def get_payment_methods_for_region(region_code: str = 'ae') -> list:
        """
        Get payment methods based on user's region
        Default to UAE (ae) if no region specified
        """
        print(f"\n=== DEBUG: Payment Methods for Region {region_code} ===")
        
        # Get regional preferences
        regional_methods = REGIONAL_PREFERENCES.get(region_code.lower(), REGIONAL_PREFERENCES['global'])
        print(f"Regional methods from config: {regional_methods}")
        
        # Convert to Stripe payment method types
        stripe_methods = []
        for method in regional_methods:
            print(f"Processing method: {method}")
            if method in PAYMENT_METHODS_CONFIG:
                stripe_type = PAYMENT_METHODS_CONFIG[method]['stripe_type']
                print(f"  -> Stripe type: {stripe_type}")
                if stripe_type not in stripe_methods:
                    stripe_methods.append(stripe_type)
                    print(f"  -> Added to stripe_methods: {stripe_type}")
                else:
                    print(f"  -> Already in stripe_methods: {stripe_type}")
            else:
                print(f"  -> WARNING: Method {method} not found in PAYMENT_METHODS_CONFIG")
        
        # Always include card as fallback
        if 'card' not in stripe_methods:
            stripe_methods.append('card')
            print(f"Added card as fallback")
            
        print(f"Final stripe_methods: {stripe_methods}")
        print("=== END DEBUG ===\n")
        return stripe_methods

    @staticmethod
    def create_customer(user: BaseUser) -> str:
        """Create a Stripe customer for a user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                metadata={
                    'user_id': user.id,
                    'is_talent': user.is_talent,
                    'is_background': user.is_background
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create Stripe customer: {str(e)}")

    @staticmethod
    def create_subscription_checkout_session(
        user: BaseUser,
        plan: SubscriptionPlan,
        success_url: str,
        cancel_url: str,
        region_code: str = 'ae'  # Default to UAE
    ) -> dict:
        """Create a Stripe checkout session for subscription"""
        try:
            print(f"Creating checkout session for user {user.id} with plan {plan.name}")
            
            # Get or create Stripe customer
            if not hasattr(user, 'stripe_customer_id'):
                print("Creating new Stripe customer")
                customer_id = StripePaymentService.create_customer(user)
                user.stripe_customer_id = customer_id
                user.save()
                print(f"Created customer with ID: {customer_id}")

            print(f"Creating Stripe checkout session with plan ID: {plan.stripe_price_id}")
            
            # Get payment methods based on user's region
            payment_method_types = StripePaymentService.get_payment_methods_for_region(region_code)
            print(f"Payment methods for region {region_code}: {payment_method_types}")
            
            # Set timeout for Stripe requests (30 seconds)
            import requests
            stripe.default_http_client = stripe.http_client.RequestsClient(timeout=30)
            
            # Validate Stripe key before making the call
            if not stripe.api_key or not stripe.api_key.startswith(('sk_test_', 'sk_live_')):
                raise Exception("Invalid Stripe configuration. Please contact support.")
            
            # Debug: Print the exact checkout session parameters
            checkout_params = {
                'customer': user.stripe_customer_id,
                'payment_method_types': payment_method_types,
                'line_items': [{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': {
                    'plan_id': str(plan.id),
                    'user_id': str(user.id)
                },
                'automatic_tax': {'enabled': True},
                'currency': 'aed',
                'customer_creation': 'always',
                'allow_promotion_codes': True,
                'payment_method_options': {
                    'card': {
                        'request_three_d_secure': 'automatic',
                    }
                },
                'payment_method_collection': 'always',
            }
            
            print(f"\n=== DEBUG: Stripe Checkout Session Parameters ===")
            print(f"Payment method types: {checkout_params['payment_method_types']}")
            print(f"Currency: {checkout_params['currency']}")
            print(f"Customer ID: {checkout_params['customer']}")
            print(f"Plan Price ID: {checkout_params['line_items'][0]['price']}")
            print("=== END DEBUG ===\n")
            
            try:
                session = stripe.checkout.Session.create(**checkout_params)
                print(f"Created session with ID: {session.id}")
                return session
            except stripe.error.AuthenticationError as e:
                print(f"Stripe authentication error: {str(e)}")
                raise Exception("Stripe authentication failed. Please contact support.")
            except stripe.error.InvalidRequestError as e:
                print(f"Stripe invalid request error: {str(e)}")
                raise Exception(f"Invalid request to Stripe: {str(e)}")
            except requests.exceptions.Timeout:
                print("Stripe request timed out")
                raise Exception("Stripe request timed out. Please try again.")
            except requests.exceptions.ConnectionError:
                print("Stripe connection error")
                raise Exception("Unable to connect to Stripe. Please try again.")
        except stripe.error.StripeError as e:
            print(f"Stripe error: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")

    @staticmethod
    def handle_webhook_event(payload: dict, sig_header: str) -> bool:
        """Handle Stripe webhook events"""
        try:
            print("\n=== Webhook Event Received ===")
            print(f"Payload: {payload}")
            print(f"Signature header: {sig_header}")
            
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            print(f"\nEvent type: {event.type}")
            
            if event.type == 'checkout.session.completed':
                session = event.data.object
                print(f"\nSession data: {session}")
                user_id = session.metadata.get('user_id')
                plan_name = session.metadata.get('plan_id')  # This is actually the plan name, e.g., 'SILVER'
                
                print(f"\nExtracted metadata:")
                print(f"User ID: {user_id}")
                print(f"Plan ID: {plan_name}")
                
                try:
                    user = BaseUser.objects.get(id=user_id)
                    plan = SubscriptionPlan.objects.get(name__iexact=plan_name.lower())
                    print(f"\nFound user: {user.email}")
                    print(f"User type - is_talent: {user.is_talent}, is_background: {user.is_background}")
                    print(f"Found plan: {plan.name}")
                    
                    # Create subscription record
                    subscription = Subscription.objects.create(
                        user=user,
                        plan=plan,
                        stripe_customer_id=session.customer,
                        stripe_subscription_id=session.subscription,
                        status='active',
                        start_date=timezone.now()
                    )
                    print(f"\nCreated subscription: {subscription.id}")
                    
                    # Update user profile based on plan
                    if user.is_talent:
                        print("\nUser is a talent user")
                        try:
                            profile = TalentUserProfile.objects.get(user=user)
                            print(f"Current account type: {profile.account_type}")
                            
                            # Handle bands plan separately - it's an add-on, not a main account type
                            if plan.name.lower() == 'bands':
                                print("Bands plan detected - this is an add-on subscription, not changing account type")
                                # Don't change the account type for bands plan
                                # The user keeps their existing account type (platinum, gold, silver, free)
                            else:
                                # Map plan name to account type for main plans
                                account_type = plan.name.lower()
                                print(f"Updating account type to: {account_type}")
                                
                                # Validate account type
                                valid_types = [choice[0] for choice in TalentUserProfile.ACCOUNT_TYPES]
                                if account_type not in valid_types:
                                    print(f"Error: Invalid account type {account_type}. Valid types are: {valid_types}")
                                    raise ValueError(f"Invalid account type: {account_type}")
                                
                                profile.account_type = account_type
                                profile.save()
                                
                                # Verify the update
                                updated_profile = TalentUserProfile.objects.get(user=user)
                                print(f"Updated account type: {updated_profile.account_type}")
                            
                        except TalentUserProfile.DoesNotExist:
                            print(f"Error: Talent profile not found for user {user.id}")
                            raise
                            
                    elif user.is_background:
                        print("\nUser is a background user")
                        try:
                            profile = BackGroundJobsProfile.objects.get(user=user)
                            print(f"Current account type: {profile.account_type}")
                            
                            # Background users should get 'back_ground_jobs' account type when they subscribe
                            account_type = 'back_ground_jobs' if plan.name == 'background_jobs' else 'free'
                            print(f"Updating account type to: {account_type}")
                            
                            # Validate account type
                            valid_types = [choice[0] for choice in BackGroundJobsProfile.ACCOUNT_TYPES]
                            if account_type not in valid_types:
                                print(f"Error: Invalid account type {account_type}. Valid types are: {valid_types}")
                                raise ValueError(f"Invalid account type: {account_type}")
                            
                            profile.account_type = account_type
                            profile.save()
                            
                            # Verify the update
                            updated_profile = BackGroundJobsProfile.objects.get(user=user)
                            print(f"Updated account type: {updated_profile.account_type}")
                            
                        except BackGroundJobsProfile.DoesNotExist:
                            print(f"Error: Background profile not found for user {user.id}")
                            raise
                    
                    return True
                    
                except BaseUser.DoesNotExist:
                    print(f"Error: User with ID {user_id} not found")
                    raise
                except SubscriptionPlan.DoesNotExist:
                    print(f"Error: Plan with ID {plan_name} not found")
                    raise
                except Exception as e:
                    print(f"Error updating profile: {str(e)}")
                    raise
                
            elif event.type in ['customer.subscription.updated', 'customer.subscription.created']:
                subscription = event.data.object
                try:
                    stripe_subscription = Subscription.objects.get(
                        stripe_subscription_id=subscription.id
                    )
                except Subscription.DoesNotExist:
                    print(f"No local subscription found for Stripe ID {subscription.id}")
                    return False
                # Always sync these fields from Stripe
                stripe_subscription.status = subscription.status
                # Update current_period_start
                if getattr(subscription, 'current_period_start', None):
                    stripe_subscription.current_period_start = dj_timezone.datetime.fromtimestamp(
                        subscription.current_period_start, tz=py_timezone.utc
                    )
                # Update current_period_end
                if getattr(subscription, 'current_period_end', None):
                    stripe_subscription.current_period_end = dj_timezone.datetime.fromtimestamp(
                        subscription.current_period_end, tz=py_timezone.utc
                    )
                # Update cancel_at_period_end
                if hasattr(subscription, 'cancel_at_period_end'):
                    stripe_subscription.cancel_at_period_end = subscription.cancel_at_period_end
                # Update end_date if canceled
                if subscription.status == 'canceled':
                    stripe_subscription.end_date = dj_timezone.now()
                stripe_subscription.save()
                print(f"Updated local subscription {stripe_subscription.id} from Stripe event.")
                return True
                
            elif event.type == 'customer.subscription.deleted':
                subscription = event.data.object
                stripe_subscription = Subscription.objects.get(
                    stripe_subscription_id=subscription.id
                )
                stripe_subscription.status = 'canceled'
                stripe_subscription.end_date = timezone.now()
                stripe_subscription.save()
                return True
                
            return False
            
        except stripe.error.SignatureVerificationError:
            print("Error: Invalid webhook signature")
            raise Exception('Invalid webhook signature')
        except Exception as e:
            print(f"Error in webhook handler: {str(e)}")
            raise Exception(f"Webhook error: {str(e)}")

    @staticmethod
    def cancel_subscription(subscription: Subscription) -> bool:
        """Cancel a Stripe subscription"""
        try:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            subscription.status = 'canceled'
            subscription.end_date = timezone.now()
            subscription.save()
            return True
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to cancel subscription: {str(e)}")

    @staticmethod
    def get_subscription_status(subscription: Subscription) -> dict:
        """Get the current status of a Stripe subscription"""
        try:
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            return {
                'status': stripe_sub.status,
                'current_period_end': stripe_sub.current_period_end,
                'cancel_at_period_end': stripe_sub.cancel_at_period_end
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to get subscription status: {str(e)}")

    @staticmethod
    def create_payment_intent(amount: int, currency: str = 'usd') -> dict:
        """Create a payment intent for one-time payments"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=['card'],
            )
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create payment intent: {str(e)}")
