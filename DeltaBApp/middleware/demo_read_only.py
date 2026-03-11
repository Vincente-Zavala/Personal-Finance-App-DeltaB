# from django.http import JsonResponse
# from django.contrib import messages
# from django.shortcuts import redirect

# class DemoReadOnlyMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # 1. Check if user is the demo user
#         if request.user.is_authenticated and request.user.username == 'demo_user':
#             # 2. Check if they are trying to "write" data
#             if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                
#                 # 3. Handle AJAX/Fetch (for your JS alert)
#                 if request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
#                    request.content_type == 'application/json':
#                     return JsonResponse({
#                         'status': 'error', 
#                         'message': 'Read-only mode: Changes are not saved in the demo.'
#                     }, status=403)
                
#                 # 4. Handle standard form submits (browser redirects)
#                 messages.warning(request, "Changes are disabled in Demo Mode.")
#                 return redirect(request.META.get('HTTP_REFERER', 'overview'))

#         return self.get_response(request)