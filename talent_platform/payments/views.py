from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import json
import stripe

from .models import SubscriptionPlan, Subscription, PaymentTransaction
from .serializers import (
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
    PaymentTransactionSerializer,
    CreateCheckoutSessionSerializer,
    CreatePaymentIntentSerializer
)
from .services import StripePaymentService

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer

class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def create_checkout_session(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        if serializer.is_valid():
            plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
            
            try:
                session = StripePaymentService.create_subscription_checkout_session(
                    user=request.user,
                    plan=plan,
                    success_url=serializer.validated_data['success_url'],
                    cancel_url=serializer.validated_data['cancel_url']
                )
                return Response({'session_id': session.id, 'url': session.url})
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        try:
            StripePaymentService.cancel_subscription(subscription)
            return Response({'status': 'subscription cancelled'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
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
