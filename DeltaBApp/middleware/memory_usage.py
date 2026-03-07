import psutil
import os
import logging
from django.utils.deprecation import MiddlewareMixin
import uuid  # For generating a request ID

process = psutil.Process(os.getpid())

def get_mem_mb():
    return process.memory_info().rss / 1024 / 1024

class MemoryUsageMiddleware(MiddlewareMixin):

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Generate a unique request ID for the request (you could also use UUID)
        request._mem_before = get_mem_mb()
        request._request_id = str(uuid.uuid4())  # Add a unique request ID for each request

    def process_response(self, request, response):
        mem_before = getattr(request, "_mem_before", None)
        request_id = getattr(request, "_request_id", "unknown")

        if mem_before is not None:
            mem_after = get_mem_mb()
            diff = mem_after - mem_before

            # Log memory usage with request ID
            logger = logging.getLogger()
            logger.info(
                f"Memory usage for request {request.path} (ID: {request_id})", 
                extra={
                    'request_id': request_id, 
                    'user': str(request.user.username) if request.user.is_authenticated else 'anonymous',
                    'memory_diff_mb': diff
                }
            )

        return response
