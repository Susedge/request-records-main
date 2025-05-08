from django.shortcuts import redirect
from django.urls import reverse

class UserTypeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If user is authenticated, apply normal routing rules
        if request.user.is_authenticated:
            # Admin users trying to access user pages get redirected to admin panel
            if request.user.user_type == 5 and request.path.startswith('/user/'):
                return redirect('/admin-panel/')
            
            # Non-admin users trying to access admin pages get redirected to user dashboard
            elif request.user.user_type != 5 and request.path.startswith('/admin-panel/'):
                return redirect('/user/dashboard/')
        # If user is not authenticated
        else:
            # Protect admin and user areas, but allow access to /request/ after registration
            if request.path.startswith('/admin-panel/') or request.path.startswith('/user/'):
                return redirect('/signup')
                
            # Check if this is a POST to /request/ (might be a new registration)
            # We don't redirect in this case to allow the registration flow to continue
            if request.path.startswith('request/') and request.method != 'POST':
                # Only redirect if it's not a POST request
                return redirect('/signup')

        response = self.get_response(request)
        return response