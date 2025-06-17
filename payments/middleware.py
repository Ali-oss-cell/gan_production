from django.utils.deprecation import MiddlewareMixin

class UserTypeThrottlingMiddleware(MiddlewareMixin):
    """
    Middleware that sets the appropriate throttle scope based on user type.
    
    This middleware examines the authenticated user and sets the request.throttle_scope
    attribute to the appropriate scope based on the user's type. This allows for
    different rate limits to be applied to different types of users.
    """
    
    def process_request(self, request):
        """
        Process the request and set the throttle scope based on user type.
        
        Args:
            request: The HTTP request object
            
        Returns:
            None: This middleware does not return a response
        """
        # Default to anonymous throttling for unauthenticated users
        if not request.user.is_authenticated:
            request.throttle_scope = 'anon'
            return
            
        # Set throttle scope based on user type
        if request.user.is_superuser or request.user.is_dashboard_admin:
            # Admin users get the highest rate limit
            request.throttle_scope = 'admin_dashboard_user'
        elif request.user.is_dashboard:
            request.throttle_scope = 'dashboard_user'
        elif request.user.is_talent:
            request.throttle_scope = 'talent_user'
        elif request.user.is_background:
            request.throttle_scope = 'background_user'
        else:
            # Default to standard user throttling for users without a specific role
            request.throttle_scope = 'user'