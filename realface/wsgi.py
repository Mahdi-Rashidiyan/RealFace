"""
WSGI config for realface project.
"""

import os
from django.core.wsgi import get_wsgi_application

# Use development settings by default
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realface.settings_dev')

# Force HTTP environment variable
os.environ['wsgi.url_scheme'] = 'http'

application = get_wsgi_application()
