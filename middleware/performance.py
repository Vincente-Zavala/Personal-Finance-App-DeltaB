import time
import traceback
from django.db import connection
from django.utils.deprecation import MiddlewareMixin


class PerformanceMiddleware(MiddlewareMixin):
    SLOW_QUERY_THRESHOLD_MS = 50     # alert threshold

    def process_request(self, request):
        """Log basic request info + start timers & query counters."""
        user = request.user.username if request.user.is_authenticated else "anon"

        print(f"[REQ] {request.method} {request.path} (user={user})", flush=True)

        # Start timer
        request._start_time = time.perf_counter()

        # Snapshot of current queries
        request._queries_before = len(connection.queries)


    def process_exception(self, request, exception):
        """Log full traceback for debugging."""
        print(f"[ERROR] {request.path}: {exception}", flush=True)
        print(traceback.format_exc(), flush=True)


    def process_response(self, request, response):
        """Compute duration + SQL queries generated during this request."""

        # === Request duration ===
        start = getattr(request, "_start_time", None)
        if start:
            duration_ms = (time.perf_counter() - start) * 1000
            print(f"[PERF] {request.path} took {duration_ms:.2f} ms", flush=True)

        # === Query diff ===
        before = getattr(request, "_queries_before", None)
        total_queries_now = len(connection.queries)
        query_count = total_queries_now - before if before is not None else 0

        if query_count > 0:
            print(f"[DB] {request.path} -> {query_count} queries", flush=True)

            # --- Identify slow queries ---
            new_queries = connection.queries[before:]
            slow = []

            for q in new_queries:
                # Django stores time as string
                q_time_ms = float(q.get("time", 0)) * 1000

                if q_time_ms > self.SLOW_QUERY_THRESHOLD_MS:
                    slow.append((q_time_ms, q["sql"]))

            # Print slow query alerts
            for ms, sql in slow:
                print(f"[DB:SLOW] ({ms:.2f} ms) {sql}", flush=True)

            # OPTIONAL: print all queries (commented out by default)
            # for q in new_queries:
            #     print(f"[DB:QUERY] ({float(q['time'])*1000:.2f} ms) {q['sql']}", flush=True)

        return response
