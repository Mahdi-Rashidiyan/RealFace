from django.http import HttpResponsePermanentRedirect
from django.conf import settings
import logging
import random
from datetime import datetime

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

class MaintenanceMiddleware:
    """Middleware to perform occasional maintenance tasks"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_cleanup = datetime.now()
        logger.info("MaintenanceMiddleware initialized")

    def __call__(self, request):
        # Run maintenance with low probability to avoid affecting every request
        # Only run for non-static requests
        if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            # 1% chance of running cleanup to avoid impacting every request
            if random.random() < 0.01:
                self._run_cleanup()
                
        # Process request normally
        return self.get_response(request)
        
    def _run_cleanup(self):
        """Run maintenance tasks"""
        try:
            # Import here to avoid circular imports
            from .tasks import cleanup_old_images, cleanup_unanalyzed_images
            
            # Clean up old images (7 days)
            cleanup_old_images(days=7)
            
            # Clean up unanalyzed images (24 hours)
            cleanup_unanalyzed_images(hours=24)
            
            # Update last cleanup time
            self.last_cleanup = datetime.now()
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")