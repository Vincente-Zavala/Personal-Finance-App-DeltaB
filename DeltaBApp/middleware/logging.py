import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django')

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        logger.info(f"Request: {request.method} {request.path} User: {request.user.username if request.user.is_authenticated else 'Unknown User'}")

    def process_response(self, request, response):
        logger.info(f"Response: {request.method} {request.path} Status: {response.status_code}")
        return response
