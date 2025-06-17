from django.shortcuts import render
from django.views.generic import TemplateView
from users.permissions import IsAdminDashboardUser, IsDashboardUser
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.mixins import LoginRequiredMixin

class RestrictedUsersView(LoginRequiredMixin, TemplateView):
    """
    View for displaying the restricted users management page.
    This page allows dashboard administrators to view and manage users from
    countries with payment restrictions (e.g., Syria).
    """
    template_name = 'dashboard/restricted_users.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Restricted Country Users'
        context['active_page'] = 'restricted_users'
        return context
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is a dashboard user or admin
        if not (request.user.is_dashboard or request.user.is_staff):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)