from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from users.permissions import IsDashboardUser, IsAdminDashboardUser
from .models import BulkEmail, EmailRecipient
from .serializers import BulkEmailSerializer, EmailRecipientSerializer, EmailListSerializer
from profiles.models import Band

class SendEmailView(APIView):
    """Send single email to one user or band creator"""
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def post(self, request, *args, **kwargs):
        """Send email to one user or band creator"""
        
        # Get data from request
        subject = request.data.get('subject', '')
        message = request.data.get('message', '')
        user_id = request.data.get('user_id')
        band_id = request.data.get('band_id')
        
        # Validation
        if not subject or not message:
            return Response(
                {'error': 'Subject and message are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if we have either user_id or band_id (but not both)
        if not user_id and not band_id:
            return Response(
                {'error': 'Either user_id or band_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user_id and band_id:
            return Response(
                {'error': 'Please provide either user_id OR band_id, not both'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_user = None
            recipient_info = {}
            
            if user_id:
                # Send to specific user
                from users.models import BaseUser
                target_user = BaseUser.objects.get(id=user_id)
                recipient_info = {
                    'type': 'user',
                    'email': target_user.email,
                    'name': f"{target_user.first_name} {target_user.last_name}".strip() or target_user.email
                }
            else:
                # Send to band creator
                band = Band.objects.get(id=band_id)
                target_user = band.creator.user
                recipient_info = {
                    'type': 'band_creator',
                    'email': target_user.email,
                    'name': f"{target_user.first_name} {target_user.last_name}".strip() or target_user.email,
                    'band_name': band.name,
                    'band_id': band.id
                }
            
            # Create email record
            email = BulkEmail.objects.create(
                sender=request.user,
                subject=subject,
                message=message,
                status='sent',
                total_recipients=1,
                sent_at=timezone.now()
            )
            
            # Create recipient record
            recipient = EmailRecipient.objects.create(
                bulk_email=email,
                user=target_user,
                status='pending'
            )
            
            # Send email
            success = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target_user.email],
                fail_silently=False,
            )
            
            if success:
                recipient.status = 'sent'
                recipient.sent_at = timezone.now()
                email.emails_sent = 1
                email.emails_failed = 0
            else:
                recipient.status = 'failed'
                recipient.error_message = 'Email sending failed'
                email.emails_sent = 0
                email.emails_failed = 1
            
            recipient.save()
            email.save()
            
            # Prepare response
            response_data = {
                'success': True,
                'message': f'Email sent to {recipient_info["email"]}',
                'recipient': recipient_info["email"],
                'recipient_name': recipient_info["name"],
                'recipient_type': recipient_info["type"],
                'status': 'sent' if success else 'failed'
            }
            
            # Add band info if sending to band creator
            if recipient_info["type"] == 'band_creator':
                response_data.update({
                    'message': f'Email sent to {recipient_info["email"]} (Creator of "{recipient_info["band_name"]}")',
                    'band_name': recipient_info["band_name"],
                    'band_id': recipient_info["band_id"],
                    'creator_name': recipient_info["name"]
                })
            
            return Response(response_data)
                
        except (BaseUser.DoesNotExist, Band.DoesNotExist) as e:
            error_msg = 'User not found' if user_id else 'Band not found'
            return Response(
                {'error': error_msg}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EmailListView(generics.ListAPIView):
    """List all emails sent by the current user"""
    serializer_class = EmailListSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get_queryset(self):
        return BulkEmail.objects.filter(sender=self.request.user).prefetch_related(
            'recipients__user'
        ).order_by('-created_at')

class EmailDetailView(generics.RetrieveAPIView):
    """Get details of a specific email and its recipient"""
    serializer_class = BulkEmailSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get_queryset(self):
        return BulkEmail.objects.filter(sender=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        # Get the email
        email = self.get_object()
        
        # Get recipient
        recipient = EmailRecipient.objects.filter(bulk_email=email).select_related('user').first()
        recipient_serializer = EmailRecipientSerializer(recipient) if recipient else None
        
        # Get email details
        email_serializer = self.get_serializer(email)
        
        return Response({
            'email': email_serializer.data,
            'recipient': recipient_serializer.data if recipient else None
        }) 