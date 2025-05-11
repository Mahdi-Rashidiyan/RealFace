from PIL import Image as PILImage
import io
from django.core.files.base import ContentFile
import gc

def optimize_image(image_file, max_size=(800, 800), quality=85):
    """
    Optimize an uploaded image for better performance while maintaining quality
    """
    img = PILImage.open(image_file)
    
    # Convert RGBA to RGB if needed
    if img.mode == 'RGBA':
        bg = PILImage.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    
    # Resize if larger than max_size while maintaining aspect ratio
    if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
        img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
    
    # Save optimized image to memory
    output = io.BytesIO()
    
    # Save with appropriate format and optimization
    format = img.format if img.format in ['JPEG', 'PNG'] else 'JPEG'
    if format == 'JPEG':
        img.save(output, format=format, quality=quality, optimize=True)
    else:  # PNG
        img.save(output, format=format, optimize=True)
    
    # Create new ContentFile from optimized image
    output.seek(0)
    content_file = ContentFile(output.read())
    
    # Clean up
    img.close()
    output.close()
    gc.collect()
    
    return content_file, format.lower()

def get_image_dimensions(image_file):
    """
    Get image dimensions safely
    """
    try:
        with PILImage.open(image_file) as img:
            return img.size
    except:
        return None