from django.http import HttpResponsePermanentRedirect
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ProtocolRedirectMiddleware:
    """Middleware to handle HTTP/HTTPS protocols appropriately in different environments.
    Only enforces HTTPS in production mode."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Log initialization
        logger.info(f"ProtocolRedirectMiddleware initialized with DEBUG={settings.DEBUG}")
        if settings.DEBUG:
            logger.info("Development mode: Protocol enforcement is DISABLED")
        else:
            logger.info("Production mode: HTTPS will be enforced")

    def __call__(self, request):
        # Skip all protocol checking in development mode
        if settings.DEBUG:
            return self.get_response(request)
            
        # In production, enforce HTTPS
        if not request.is_secure():
            # Redirect to HTTPS in production only
            domain = request.get_host().split(':')[0]
            redirect_url = f'https://{domain}{request.get_full_path()}'
            logger.debug(f"Redirecting to HTTPS: {redirect_url}")
            return HttpResponsePermanentRedirect(redirect_url)
        
        # Otherwise, handle the request normally
        return self.get_response(request)