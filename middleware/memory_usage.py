import psutil, os
from django.utils.deprecation import MiddlewareMixin

process = psutil.Process(os.getpid())

def get_mem_mb():
    return process.memory_info().rss / 1024 / 1024

class MemoryUsageMiddleware(MiddlewareMixin):

    def process_view(self, request, view_func, view_args, view_kwargs):
        request._mem_before = get_mem_mb()

    def process_response(self, request, response):
        mem_before = getattr(request, "_mem_before", None)

        if mem_before is not None:
            mem_after = get_mem_mb()
            diff = mem_after - mem_before

            print(
                f"[MEM] View {request.path} used {diff:.2f} MB"
                f"(before={mem_before:.2f} MB, after={mem_after: .2f} MB)"
                )

        return response
