from django.http import HttpResponsePermanentRedirect
from django.conf import settings

class ProtocolRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG and not request.is_secure():
            # Redirect to HTTPS in production only
            domain = request.get_host().split(':')[0]
            return HttpResponsePermanentRedirect(
                f'https://{domain}{request.get_full_path()}'
            )
        elif settings.DEBUG and request.is_secure():
            # Redirect to HTTP in development only
            domain = request.get_host().split(':')[0]
            return HttpResponsePermanentRedirect(
                f'http://{domain}:8000{request.get_full_path()}'
            )
        
        return self.get_response(request)