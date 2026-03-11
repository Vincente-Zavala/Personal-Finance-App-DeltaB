import psutil
import os
import logging
import uuid
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)
process = psutil.Process(os.getpid())

def get_mem_mb():
    return process.memory_info().rss / 1024 / 1024

class MemoryUsageMiddleware(MiddlewareMixin):

    def process_view(self, request, view_func, view_args, view_kwargs):

        if not hasattr(request, '_request_id'):
            request._request_id = str(uuid.uuid4())
        
        request._mem_before = get_mem_mb()

    def process_response(self, request, response):
        mem_before = getattr(request, "_mem_before", None)
        request_id = getattr(request, "_request_id", "unknown")

        if mem_before is not None:
            mem_after = get_mem_mb()
            diff = mem_after - mem_before

            logger.info(
                f"Memory usage for request {request.path} (ID: {request_id})", 
                extra={
                    'request_id': request_id, 
                    'user': str(request.user.username) if request.user.is_authenticated else 'anonymous',
                    'memory_diff_mb': diff
                }
            )

        return response