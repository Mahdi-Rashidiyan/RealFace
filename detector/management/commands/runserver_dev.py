from django.core.management.commands.runserver import Command as RunServerCommand
from django.core.management.base import CommandError
import os

class Command(RunServerCommand):
    help = 'Run development server with HTTP forced'

    def handle(self, *args, **options):
        # Force development settings
        os.environ['DJANGO_SETTINGS_MODULE'] = 'realface.settings_dev'
        os.environ['wsgi.url_scheme'] = 'http'
        
        # Disable SSL redirect
        os.environ['SECURE_SSL_REDIRECT'] = 'False'
        os.environ['SESSION_COOKIE_SECURE'] = 'False'
        os.environ['CSRF_COOKIE_SECURE'] = 'False'
        
        # Set debug mode
        os.environ['DEBUG'] = 'True'
        
        try:
            super().handle(*args, **options)
        except CommandError as e:
            # Handle any server startup errors
            self.stderr.write(self.style.ERROR(str(e)))