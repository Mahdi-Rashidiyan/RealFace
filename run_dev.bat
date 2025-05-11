@echo off
echo ======================================
echo RealFace Development Server
echo ======================================
echo.
echo Starting local development server on port 8080...
echo.
echo IMPORTANT: Access the application at:
echo http://localhost:8080
echo.
echo DO NOT use 127.0.0.1, use localhost instead
echo DO NOT attempt to use HTTPS
echo.
echo Press Ctrl+C to stop the server.
echo ======================================
echo.

set DJANGO_SETTINGS_MODULE=realface.settings_dev
set DEBUG=True
set SECURE_SSL_REDIRECT=False
set SESSION_COOKIE_SECURE=False
set CSRF_COOKIE_SECURE=False

python manage.py runserver 8080

pause 