import time
import traceback
import uuid
import logging
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

class PerformanceMiddleware(MiddlewareMixin):
    SLOW_QUERY_THRESHOLD_MS = 50  # alert threshold

    def process_request(self, request):
        """Log basic request info + start timers & query counters."""
        user = request.user.username if request.user.is_authenticated else "anon"
        request._start_time = time.perf_counter()
        request._queries_before = len(connection.queries)
        request._request_id = str(uuid.uuid4())  # Add request ID for each request

        logger = logging.getLogger()
        logger.info(f"Request {request.method} {request.path} (user={user})",
                    extra={'request_id': request._request_id, 'user': user})

    def process_exception(self, request, exception):
        """Log full traceback for debugging."""
        request_id = getattr(request, '_request_id', 'unknown')
        logger = logging.getLogger()
        logger.error(f"Exception occurred at {request.path} (ID: {request_id})", 
                     extra={'request_id': request_id, 'exception': str(exception)})

        # Optional: print the full traceback to the console (or log it)
        print(traceback.format_exc(), flush=True)

    def process_response(self, request, response):
        """Log performance + SQL queries."""

        # === Request duration ===
        start = getattr(request, "_start_time", None)
        if start:
            duration_ms = (time.perf_counter() - start) * 1000
            logger = logging.getLogger()
            logger.info(f"Request {request.path} took {duration_ms:.2f} ms", 
                        extra={'request_id': request._request_id, 'duration_ms': duration_ms})

        # === Query diff ===
        before = getattr(request, "_queries_before", None)
        total_queries_now = len(connection.queries)
        query_count = total_queries_now - before if before is not None else 0

        if query_count > 0:
            logger = logging.getLogger()
            logger.info(f"Request {request.path} executed {query_count} SQL queries",
                        extra={'request_id': request._request_id, 'query_count': query_count})

            # Log slow queries
            new_queries = connection.queries[before:]
            slow = []

            for q in new_queries:
                q_time_ms = float(q.get("time", 0)) * 1000
                if q_time_ms > self.SLOW_QUERY_THRESHOLD_MS:
                    slow.append((q_time_ms, q["sql"]))

            for ms, sql in slow:
                logger.warning(f"Slow query detected: ({ms:.2f} ms) {sql}",
                               extra={'request_id': request._request_id, 'sql': sql, 'slow_ms': ms})

        return response
