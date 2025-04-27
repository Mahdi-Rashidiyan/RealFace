from django.shortcuts import render
from django.http import JsonResponse
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

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def home(request):
    """Render the home page"""
    return render(request, 'detector/home.html')

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
