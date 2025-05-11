from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from cache_memoize import cache_memoize
from .models import Image
from .ai_model import analyzer
import os
import logging
import traceback
import hashlib
import psutil
import sys

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def home(request):
    """Render the home page"""
    return render(request, 'detector/home.html')

def debug_info(request):
    """Development only view to help debug connection issues"""
    if not settings.DEBUG:
        return HttpResponse("Debug view only available in development mode", status=403)
    
    is_secure = request.is_secure()
    protocol = "HTTPS" if is_secure else "HTTP"
    
    # Check headers
    headers = dict(request.headers)
    important_headers = {
        'Host': headers.get('Host', 'Not set'),
        'X-Forwarded-Proto': headers.get('X-Forwarded-Proto', 'Not set'),
        'X-Forwarded-For': headers.get('X-Forwarded-For', 'Not set'),
        'User-Agent': headers.get('User-Agent', 'Not set')
    }
    
    # System info
    debug_info = {
        'Protocol': protocol,
        'Is Secure': is_secure,
        'Host': request.get_host(),
        'Path': request.path,
        'GET Parameters': dict(request.GET),
        'Important Headers': important_headers,
        'All Headers': headers,
        'Django Settings': {
            'DEBUG': settings.DEBUG,
            'SECURE_SSL_REDIRECT': getattr(settings, 'SECURE_SSL_REDIRECT', 'Not set'),
            'SESSION_COOKIE_SECURE': getattr(settings, 'SESSION_COOKIE_SECURE', 'Not set'),
            'CSRF_COOKIE_SECURE': getattr(settings, 'CSRF_COOKIE_SECURE', 'Not set'),
        }
    }
    
    # Render debug template
    context = {
        'debug_info': debug_info,
        'title': 'Connection Debug Info'
    }
    
    return render(request, 'detector/debug.html', context)

def health_check(request):
    """Health check endpoint for Render"""
    # Check if media directory exists and is writeable
    media_dir_exists = os.path.exists(settings.MEDIA_ROOT)
    media_dir_writable = os.access(settings.MEDIA_ROOT, os.W_OK) if media_dir_exists else False
    
    # Get memory usage for debugging
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    
    health_data = {
        'status': 'ok',
        'message': 'Service is healthy',
        'python_version': sys.version,
        'media_directory': {
            'path': settings.MEDIA_ROOT,
            'exists': media_dir_exists,
            'writable': media_dir_writable
        },
        'memory': {
            'total_mb': round(memory_info.total / (1024 * 1024), 2),
            'available_mb': round(memory_info.available / (1024 * 1024), 2),
            'used_percent': memory_info.percent
        },
        'disk': {
            'total_gb': round(disk_info.total / (1024 * 1024 * 1024), 2),
            'free_gb': round(disk_info.free / (1024 * 1024 * 1024), 2),
            'used_percent': disk_info.percent
        }
    }
    
    return JsonResponse(health_data)

def get_image_hash(image_file):
    """Generate a hash for the image content"""
    hasher = hashlib.md5()
    for chunk in image_file.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()

@cache_memoize(timeout=3600)  # Cache analysis results for 1 hour
def analyze_image_content(image_path):
    """Analyze image content with caching"""
    try:
        return analyzer.analyze_image(image_path)
    except Exception as e:
        logger.error(f"Error in analyze_image_content: {str(e)}\n{traceback.format_exc()}")
        return None

@require_http_methods(["POST"])
def analyze_image(request):
    """Handle image upload and analysis with rate limiting"""
    # Check for rate limit (handled by middleware)
    if getattr(request, 'limited', False):
        return JsonResponse({
            'status': 'error',
            'message': 'Rate limit exceeded. Please wait before trying again.'
        }, status=429)

    if not request.FILES.get('image'):
        return JsonResponse({
            'status': 'error',
            'message': 'No image file provided'
        }, status=400)

    image_file = request.FILES['image']
    
    try:
        # Check file size for Render's free tier
        max_size = 5 * 1024 * 1024  # 5MB for Render
        if image_file.size > max_size:
            return JsonResponse({
                'status': 'error',
                'message': f'Image file size exceeds the maximum allowed ({max_size/1024/1024:.1f}MB)'
            }, status=400)
            
        # Generate hash for the image content
        image_hash = get_image_hash(image_file)
        
        # Check if we have cached results for this image
        cached_result = cache.get(f'analysis_{image_hash}')
        if cached_result:
            return JsonResponse(cached_result)

        # Create and save image instance (this will trigger validation)
        img_instance = Image.objects.create(image=image_file)
        
        # Get the full path of the saved image
        image_path = os.path.join(settings.MEDIA_ROOT, img_instance.image.name)
        
        # Analyze the image using our AI model with caching
        try:
            result = analyze_image_content(image_path)
            
            if result:
                img_instance.is_real = result['is_real']
                img_instance.confidence_score = result['confidence']
                img_instance.analysis_result = 'Real Image' if result['is_real'] else 'AI Generated'
                img_instance.save()
                
                response_data = {
                    'status': 'success',
                    'result': img_instance.analysis_result,
                    'confidence': result['confidence'],
                    'image_url': img_instance.image.url,
                    'details': {
                        'size': img_instance.file_size,
                        'width': img_instance.image_width,
                        'height': img_instance.image_height,
                        'filename': img_instance.original_filename
                    }
                }
                
                # Cache the results
                cache.set(f'analysis_{image_hash}', response_data, timeout=3600)
                
                return JsonResponse(response_data)
            else:
                raise Exception("Analysis failed to produce a result")
                
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}\n{traceback.format_exc()}")
            # Delete the uploaded file if analysis fails
            img_instance.delete()
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to analyze image. Please try again.'
            }, status=500)
            
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.'
        }, status=500)
