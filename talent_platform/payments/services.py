import stripe
from django.conf import settings
from django.utils import timezone
from .models import SubscriptionPlan, Subscription, PaymentTransaction
from profiles.models import TalentUserProfile, BackGroundJobsProfile
from users.models import BaseUser

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripePaymentService:
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
        cancel_url: str
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
            session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'plan_id': str(plan.id),  # Ensure plan_id is a string
                    'user_id': str(user.id)   # Ensure user_id is a string
                }
            )
            print(f"Created session with ID: {session.id}")
            return session
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
                            
                            # Map plan name to account type
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
                            
                            account_type = 'back_ground_jobs' if plan.name == 'back_ground_jobs' else 'free'
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
                
            elif event.type == 'customer.subscription.updated':
                subscription = event.data.object
                stripe_subscription = Subscription.objects.get(
                    stripe_subscription_id=subscription.id
                )
                
                if subscription.status == 'active':
                    stripe_subscription.status = 'active'
                elif subscription.status == 'canceled':
                    stripe_subscription.status = 'canceled'
                    stripe_subscription.end_date = timezone.now()
                
                stripe_subscription.save()
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
