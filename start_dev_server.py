#!/usr/bin/env python
"""
Simple script to run Django development server with HTTP-only settings.
This avoids HTTPS redirection issues in local development.
"""

import os
import sys
import django
from django.core.management import call_command

if __name__ == "__main__":
    # Force development settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realface.settings_dev")
    
    # Force HTTP
    os.environ["wsgi.url_scheme"] = "http"
    os.environ["SECURE_SSL_REDIRECT"] = "False"
    os.environ["SESSION_COOKIE_SECURE"] = "False"
    os.environ["CSRF_COOKIE_SECURE"] = "False"
    
    # Set debug mode
    os.environ["DEBUG"] = "True"
    
    # Initialize Django
    django.setup()
    
    # Run the development server
    try:
        print("Starting development server on http://127.0.0.1:8000/")
        print("HTTPS is disabled for local development.")
        print("Press Ctrl+C to stop the server.")
        sys.argv = ["manage.py", "runserver"]
        call_command("runserver")
    except KeyboardInterrupt:
        print("\nServer stopped.") 