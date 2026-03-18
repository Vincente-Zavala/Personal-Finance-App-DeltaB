import time
import logging
import uuid
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class PerformanceMiddleware(MiddlewareMixin):
    SLOW_QUERY_THRESHOLD_MS = 50

    def process_request(self, request):
        request._start_time = time.perf_counter()
        request._queries_before = len(connection.queries)

        if not hasattr(request, '_request_id'):
            request._request_id = str(uuid.uuid4())

    def process_exception(self, request, exception):
        request_id = getattr(request, '_request_id', 'unknown')

        logger.exception(f"Exception at {request.path}", extra={'request_id': request_id})

    def process_response(self, request, response):
            request_id = getattr(request, '_request_id', 'unknown')
            start = getattr(request, "_start_time", None)
            
            user_display = "Anonymous"
            if hasattr(request, '_cached_user'):
                user = request.user
                if user.is_authenticated:
                    user_display = user.username


            if start:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    f"Performance: {duration_ms:.2f}ms | User: {user_display}", 
                    extra={
                        'request_id': request_id, 
                        'duration_ms': duration_ms,
                        'user': user_display
                    }
                )

            try:
                before = getattr(request, "_queries_before", 0)
                queries = connection.queries[before:]
                query_count = len(queries)
                
                if query_count > 0:
                    logger.info(f"SQL: {query_count} queries executed",
                                extra={'request_id': request_id, 'query_count': query_count})
                    
                    for q in queries:
                        try:
                            ms = float(q.get("time", 0)) * 1000
                            if ms > self.SLOW_QUERY_THRESHOLD_MS:
                                logger.warning(f"SLOW SQL: {ms:.2f}ms | {q['sql']}",
                                            extra={'request_id': request_id})
                        except (TypeError, ValueError):
                            continue
            except Exception as e:
                logger.error(f"Error in SQL analysis: {e}")

            return response