from django.http import HttpResponseForbidden

class BanHTTPMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, request):

        return HttpResponseForbidden("ERROR: no http request allowed")