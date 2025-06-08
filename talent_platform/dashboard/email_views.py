from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator

from users.permissions import IsDashboardUser, IsAdminDashboardUser
from .models import BulkEmail, EmailRecipient
from .email_service import DashboardEmailService
from .serializers import BulkEmailSerializer, EmailRecipientSerializer

class BulkEmailView(APIView):
    """Create and send bulk emails to selected users"""
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def post(self, request, *args, **kwargs):
        """Create and send bulk email to selected user IDs"""
        
        # Get data from request
        subject = request.data.get('subject', '')
        message = request.data.get('message', '')
        user_ids = request.data.get('user_ids', [])
        search_criteria = request.data.get('search_criteria', {})
        send_immediately = request.data.get('send_immediately', True)
        
        # Validation
        if not subject or not message:
            return Response(
                {'error': 'Subject and message are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user_ids:
            return Response(
                {'error': 'At least one user must be selected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create bulk email record
            bulk_email = DashboardEmailService.create_bulk_email(
                sender=request.user,
                subject=subject,
                message=message,
                search_criteria=search_criteria
            )
            
            # Add recipients
            recipients = DashboardEmailService.add_recipients(bulk_email, user_ids)
            
            if send_immediately:
                # Send emails
                result = DashboardEmailService.send_bulk_email(bulk_email.id)
                
                return Response({
                    'success': True,
                    'bulk_email_id': bulk_email.id,
                    'message': f'Email sent to {result["emails_sent"]} users',
                    'emails_sent': result['emails_sent'],
                    'emails_failed': result['emails_failed'],
                    'total_recipients': result['total_recipients']
                })
            else:
                return Response({
                    'success': True,
                    'bulk_email_id': bulk_email.id,
                    'message': f'Email saved as draft with {len(recipients)} recipients',
                    'total_recipients': len(recipients)
                })
                
        except Exception as e:
            return Response(
                {'error': f'Failed to create bulk email: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SendDraftEmailView(APIView):
    """Send a previously created draft email"""
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def post(self, request, bulk_email_id, *args, **kwargs):
        """Send a draft bulk email"""
        
        try:
            bulk_email = get_object_or_404(BulkEmail, id=bulk_email_id, sender=request.user)
            
            if bulk_email.status != 'draft':
                return Response(
                    {'error': 'Email has already been sent or is not a draft'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Send the email
            result = DashboardEmailService.send_bulk_email(bulk_email.id)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': f'Email sent to {result["emails_sent"]} users',
                    'emails_sent': result['emails_sent'],
                    'emails_failed': result['emails_failed'],
                    'total_recipients': result['total_recipients']
                })
            else:
                return Response(
                    {'error': result['error']}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class BulkEmailListView(generics.ListAPIView):
    """List all bulk emails sent by the current user"""
    serializer_class = BulkEmailSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get_queryset(self):
        return BulkEmail.objects.filter(sender=self.request.user)

class BulkEmailDetailView(generics.RetrieveAPIView):
    """Get details of a specific bulk email"""
    serializer_class = BulkEmailSerializer
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get_queryset(self):
        return BulkEmail.objects.filter(sender=self.request.user)

class EmailRecipientsView(APIView):
    """Get recipients for a specific bulk email"""
    permission_classes = [IsDashboardUser | IsAdminDashboardUser]
    
    def get(self, request, bulk_email_id, *args, **kwargs):
        """Get paginated list of recipients for a bulk email"""
        
        bulk_email = get_object_or_404(BulkEmail, id=bulk_email_id, sender=request.user)
        
        recipients = EmailRecipient.objects.filter(bulk_email=bulk_email).select_related('user')
        
        # Pagination
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 20)
        
        paginator = Paginator(recipients, per_page)
        page_obj = paginator.get_page(page)
        
        serializer = EmailRecipientSerializer(page_obj.object_list, many=True)
        
        return Response({
            'recipients': serializer.data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_recipients': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })

@api_view(['GET'])
@permission_classes([IsDashboardUser | IsAdminDashboardUser])
def email_statistics(request, bulk_email_id):
    """Get statistics for a bulk email campaign"""
    
    bulk_email = get_object_or_404(BulkEmail, id=bulk_email_id, sender=request.user)
    
    stats = DashboardEmailService.get_email_statistics(bulk_email_id)
    
    if stats:
        return JsonResponse(stats)
    else:
        return JsonResponse({'error': 'Email statistics not found'}, status=404) 