# permissions.py
from rest_framework.permissions import BasePermission

class IsTalentUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_talent  # Only allow Talent users

class IsBackgroundUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_background  # Only allow Background users

class IsDashboardUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_dashboard  # Only allow Dashboard users

class IsAdminDashboardUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_dashboard_admin  # Only allow Dashboard Admin users
