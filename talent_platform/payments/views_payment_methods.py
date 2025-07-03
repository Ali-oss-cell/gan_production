from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from decimal import Decimal

from .payment_services import PaymentMethodService, ApplePayService, GooglePayService
from .payment_methods_config import get_regional_preferences, is_payment_method_supported
from .models import PaymentMethodSupport

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_payment_methods(request):
    """Get available payment methods for the user"""
    try:
        # Get user's region (you might need to adjust this based on your user model)
        region = getattr(request.user, 'country', 'us').lower()
        amount = request.GET.get('amount')
        currency = request.GET.get('currency', 'USD')
        
        if amount:
            try:
                amount = Decimal(amount)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid amount provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get available methods
        available_methods = PaymentMethodService.get_available_methods(
            request.user, amount, currency
        )
        
        # Get regional preferences for ordering
        regional_prefs = get_regional_preferences(region)
        
        # Order methods by regional preference
        ordered_methods = []
        for method in regional_prefs:
            if method in available_methods:
                ordered_methods.append(method)
        
        # Add any remaining methods
        for method in available_methods:
            if method not in ordered_methods:
                ordered_methods.append(method)
        
        # Get detailed information for each method
        method_details = []
        for method in ordered_methods:
            support = PaymentMethodSupport.objects.filter(
                payment_method=method,
                region__in=[region, 'global'],
                currency=currency,
                is_active=True
            ).first()
            
            if support:
                method_details.append({
                    'method': method,
                    'name': support.get_payment_method_display(),
                    'min_amount': float(support.min_amount) if support.min_amount else None,
                    'max_amount': float(support.max_amount) if support.max_amount else None,
                    'processing_fee': float(support.processing_fee),
                    'fixed_fee': float(support.fixed_fee),
                    'description': support.notes,
                    'stripe_type': support.stripe_payment_method_type,
                })
        
        return Response({
            'region': region,
            'currency': currency,
            'payment_methods': method_details
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """Create a payment intent for a specific payment method"""
    try:
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'card')
        currency = request.data.get('currency', 'USD')
        metadata = request.data.get('metadata', {})
        
        if not amount:
            return Response(
                {'error': 'Amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(amount)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create payment intent
        intent_data = PaymentMethodService.create_payment_intent(
            request.user, amount, currency, payment_method, metadata
        )
        
        return Response(intent_data)
        
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request):
    """Confirm a payment intent"""
    try:
        payment_intent_id = request.data.get('payment_intent_id')
        payment_method_id = request.data.get('payment_method_id')
        
        if not payment_intent_id:
            return Response(
                {'error': 'Payment intent ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Confirm payment
        PaymentMethodService.confirm_payment(payment_intent_id, payment_method_id)
        
        return Response({'status': 'Payment confirmed successfully'})
        
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_apple_pay_config(request):
    """Get Apple Pay configuration"""
    try:
        # This would typically include domain verification and other Apple Pay specific config
        config = {
            'merchant_id': getattr(settings, 'APPLE_PAY_MERCHANT_ID', ''),
            'domain_verification_url': f"{request.scheme}://{request.get_host()}/.well-known/apple-developer-merchantid-domain-association",
            'supported_networks': ['visa', 'mastercard', 'amex'],
            'merchant_capabilities': ['supports3DS'],
        }
        
        return Response(config)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_google_pay_config(request):
    """Get Google Pay configuration"""
    try:
        config = GooglePayService.get_google_pay_configuration()
        return Response(config)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_method_details(request, payment_method_id):
    """Get details of a specific payment method"""
    try:
        details = PaymentMethodService.get_payment_method_details(payment_method_id)
        
        # Only return safe information
        safe_details = {
            'id': details.id,
            'type': details.type,
            'card': {
                'brand': details.card.brand,
                'last4': details.card.last4,
                'exp_month': details.card.exp_month,
                'exp_year': details.card.exp_year,
            } if details.type == 'card' else None,
            'billing_details': details.billing_details,
        }
        
        return Response(safe_details)
        
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def attach_payment_method(request):
    """Attach a payment method to a customer"""
    try:
        payment_method_id = request.data.get('payment_method_id')
        customer_id = request.data.get('customer_id')
        
        if not payment_method_id or not customer_id:
            return Response(
                {'error': 'Payment method ID and customer ID are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        PaymentMethodService.attach_payment_method_to_customer(payment_method_id, customer_id)
        
        return Response({'status': 'Payment method attached successfully'})
        
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def detach_payment_method(request, payment_method_id):
    """Detach a payment method from a customer"""
    try:
        PaymentMethodService.detach_payment_method(payment_method_id)
        
        return Response({'status': 'Payment method detached successfully'})
        
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 