from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import json
import stripe
from rest_framework.views import APIView
from .pricing_config import (
    SUBSCRIPTION_PLANS,
    ADDITIONAL_SERVICES,
    PROMOTIONS,
    CURRENCY,
    CURRENCY_SYMBOL,
    PAYMENT_SETTINGS
)
from users.permissions import IsTalentUser, IsBackgroundUser

from .models import SubscriptionPlan, Subscription, PaymentTransaction
from .serializers import (
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
    PaymentTransactionSerializer,
    CreateCheckoutSessionSerializer,
    CreatePaymentIntentSerializer
)
from .services import StripePaymentService

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing subscription plans.
    Plans are filtered based on user profile type:
    - Talent profiles must choose one of: Silver, Gold, or Platinum
    - Talent profiles can optionally add Bands plan
    - Background profiles can only choose Background Jobs plan
    """
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        elif self.action in ['list', 'retrieve', 'features', 'pricing']:
            # Only allow authenticated users to view plans
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter plans based on user profile type and subscription rules
        """
        queryset = SubscriptionPlan.objects.all()
        
        # If user is not authenticated, show all active plans
        if not self.request.user.is_authenticated:
            return queryset.filter(is_active=True)
        
        # Check user type and filter plans accordingly
        if hasattr(self.request.user, 'is_talent') and self.request.user.is_talent:
            # For talent users, show main plans (silver, gold, platinum) and bands
            queryset = queryset.filter(
                name__in=['silver', 'gold', 'platinum', 'bands']
            )
            
            # Check if user already has a main plan subscription
            has_main_plan = Subscription.objects.filter(
                user=self.request.user,
                plan__name__in=['silver', 'gold', 'platinum'],
                is_active=True
            ).exists()
            
            # If user has a main plan, only show bands plan
            if has_main_plan:
                queryset = queryset.filter(name='bands')
            
        elif hasattr(self.request.user, 'is_background') and self.request.user.is_background:
            # For background users, only show background jobs plan
            queryset = queryset.filter(name='back_ground_jobs')
        
        # Filter by active status if specified
        active_only = self.request.query_params.get('active_only', None)
        if active_only is not None:
            queryset = queryset.filter(is_active=True)
            
        return queryset

    @action(detail=True, methods=['get'])
    def features(self, request, pk=None):
        """
        Get detailed features of a specific plan
        """
        plan = self.get_object()
        plan_config = SUBSCRIPTION_PLANS.get(plan.name.upper())
        if not plan_config:
            return Response(
                {'error': 'Plan configuration not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({
            'plan': plan.name,
            'features': plan_config['features']
        })

    @action(detail=False, methods=['get'])
    def pricing(self, request):
        """
        Get all plans with their pricing information
        """
        plans = self.get_queryset()
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_subscription(self, request):
        """
        Create a new subscription with validation rules
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.validated_data['plan']
            
            # Validate plan selection based on user type
            if hasattr(request.user, 'is_talent') and request.user.is_talent:
                # For talent users
                if plan.name == 'bands':
                    # Allow bands plan to be added to any existing plan
                    pass
                else:
                    # Check if user already has a main plan
                    has_main_plan = Subscription.objects.filter(
                        user=request.user,
                        plan__name__in=['silver', 'gold', 'platinum'],
                        is_active=True
                    ).exists()
                    
                    if has_main_plan:
                        return Response(
                            {'error': 'You already have a main plan subscription'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            
            elif hasattr(request.user, 'is_background') and request.user.is_background:
                # For background users, only allow background jobs plan
                if plan.name != 'back_ground_jobs':
                    return Response(
                        {'error': 'Background users can only subscribe to the Background Jobs plan'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create the subscription
            subscription = serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        """
        Create a new subscription plan
        Only accessible by admin users
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Update an existing subscription plan
        Only accessible by admin users
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete a subscription plan
        Only accessible by admin users
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user subscriptions.
    
    This viewset provides the following actions:
    - List all subscriptions for the authenticated user
    - Retrieve a specific subscription
    - Create a new subscription
    - Update an existing subscription
    - Delete a subscription
    - Create a checkout session for subscription
    - Cancel a subscription
    - Get subscription status
    
    Authentication:
    - All actions require authentication
    - Users can only access their own subscriptions
    
    Permissions:
    - Uses IsAuthenticated permission class
    - Users can only view and modify their own subscriptions
    
    Endpoints:
    GET /api/payments/subscriptions/ - List all subscriptions
    GET /api/payments/subscriptions/{id}/ - Get specific subscription
    POST /api/payments/subscriptions/ - Create new subscription
    PUT /api/payments/subscriptions/{id}/ - Update subscription
    DELETE /api/payments/subscriptions/{id}/ - Delete subscription
    POST /api/payments/subscriptions/create_checkout_session/ - Create checkout session
    POST /api/payments/subscriptions/{id}/cancel/ - Cancel subscription
    GET /api/payments/subscriptions/{id}/status/ - Get subscription status
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter subscriptions to only show those belonging to the authenticated user.
        
        Returns:
            QuerySet: Filtered subscriptions for the current user
        """
        return Subscription.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def create_checkout_session(self, request):
        """
        Create a Stripe checkout session for subscription.
        
        This action:
        1. Validates the plan_id and URLs
        2. Creates a Stripe checkout session
        3. Returns the session ID and URL for redirection
        
        Request body:
        {
            "plan_id": int,  # ID of the subscription plan
            "success_url": str,  # URL to redirect after successful payment
            "cancel_url": str  # URL to redirect if payment is cancelled
        }
        
        Returns:
            Response: Contains session_id and URL for Stripe checkout
        """
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
                success_url = serializer.validated_data.get('success_url')
                cancel_url = serializer.validated_data.get('cancel_url')

                session = StripePaymentService.create_subscription_checkout_session(
                    user=request.user,
                    plan=plan,
                    success_url=success_url,
                    cancel_url=cancel_url
                )
                return Response({'session_id': session.id, 'url': session.url})
            except SubscriptionPlan.DoesNotExist:
                return Response({'error': 'Invalid plan ID'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an active subscription.
        
        This action:
        1. Retrieves the subscription
        2. Calls Stripe to cancel the subscription
        3. Updates the subscription status in the database
        
        Returns:
            Response: Success status of the cancellation
        """
        subscription = self.get_object()
        try:
            StripePaymentService.cancel_subscription(subscription)
            return Response({'status': 'subscription cancelled'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Get the current status of a subscription.
        
        This action:
        1. Retrieves the subscription
        2. Gets the current status from Stripe
        3. Returns detailed status information
        
        Returns:
            Response: Current subscription status including:
            - status (active, canceled, etc.)
            - current_period_end
            - cancel_at_period_end
        """
        subscription = self.get_object()
        try:
            status = StripePaymentService.get_subscription_status(subscription)
            return Response(status)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentTransaction.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        serializer = CreatePaymentIntentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                intent = StripePaymentService.create_payment_intent(
                    amount=serializer.validated_data['amount'],
                    currency=serializer.validated_data['currency']
                )
                return Response(intent)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        StripePaymentService.handle_webhook_event(payload, sig_header)
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(str(e), status=400)

class PricingView(APIView):
    """
    API endpoint that provides pricing information for the frontend.
    """
    def get(self, request):
        try:
            # Format subscription plans data
            subscription_plans = {
                plan_key: {
                    'name': plan['name'],
                    'price': str(plan['price']),  # Convert Decimal to string for JSON
                    'features': plan['features'],
                    'duration_months': plan['duration_months'],
                    'stripe_price_id': plan['stripe_price_id'],
                    'monthly_equivalent': str(plan['price'] / plan['duration_months']),  # Calculate monthly price
                }
                for plan_key, plan in SUBSCRIPTION_PLANS.items()
            }

            # Format additional services data
            additional_services = {
                service_key: {
                    'name': service['name'],
                    'price': str(service['price']),
                    'description': service['description'],
                    'stripe_price_id': service['stripe_price_id'],
                }
                for service_key, service in ADDITIONAL_SERVICES.items()
            }

            # Format promotions data
            promotions = {
                promo_key: {
                    'name': promo['name'],
                    'discount_percentage': promo['discount_percentage'],
                    'description': promo['description'],
                    'duration_days': promo.get('duration_days', None),
                }
                for promo_key, promo in PROMOTIONS.items()
            }

            response_data = {
                'subscription_plans': subscription_plans,
                'additional_services': additional_services,
                'promotions': promotions,
                'currency': {
                    'code': CURRENCY,
                    'symbol': CURRENCY_SYMBOL,
                },
                'payment_settings': {
                    'minimum_payment': str(PAYMENT_SETTINGS['MINIMUM_PAYMENT']),
                    'maximum_payment': str(PAYMENT_SETTINGS['MAXIMUM_PAYMENT']),
                    'refund_policy_days': PAYMENT_SETTINGS['REFUND_POLICY_DAYS'],
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            plan_id = request.data.get('plan_id')
            success_url = request.data.get('success_url')
            cancel_url = request.data.get('cancel_url')

            if not all([plan_id, success_url, cancel_url]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if plan_id not in SUBSCRIPTION_PLANS:
                return Response(
                    {'error': 'Invalid plan ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            plan = SUBSCRIPTION_PLANS[plan_id]
            
            # Create Stripe checkout session
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': plan['name'],
                        },
                        'unit_amount': int(plan['price'] * 100),  # Convert to cents
                        'recurring': {
                            'interval': 'year'
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=request.user.email,
                metadata={
                    'user_id': str(request.user.id),
                    'plan_id': plan_id
                }
            )

            return Response({
                'session_id': session.id,
                'url': session.url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
