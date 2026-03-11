from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def demo_read_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check for your guest/demo user
        if request.user.is_authenticated and request.user.username == 'demo_user':
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                
                # Check for AJAX/Fetch
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
                   request.content_type == 'application/json':
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Read-only mode: Changes are not saved in the demo.'
                    }, status=403) # 403 ensures response.ok is false
                
                # Standard Form Redirect
                messages.warning(request, "Changes are disabled in Demo Mode.")
                return redirect(request.META.get('HTTP_REFERER', 'overview'))
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view