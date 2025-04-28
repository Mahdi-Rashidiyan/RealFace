from django.db import models
from django.core.exceptions import ValidationError
import uuid
import os
from PIL import Image as PILImage
import mimetypes
from .utils import optimize_image, get_image_dimensions

def validate_image_file(upload):
    # Check file size (max 10MB)
    if upload.size > 10 * 1024 * 1024:
        raise ValidationError('Image file size must be under 10MB')
    
    # Check file type using mimetypes
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    file_type, _ = mimetypes.guess_type(upload.name)
    if not file_type or file_type not in allowed_types:
        raise ValidationError('Unsupported file type. Please upload JPEG, PNG, or WebP images')
    
    try:
        # Try opening the image to verify it's not corrupted
        img = PILImage.open(upload)
        img.verify()
    except Exception:
        raise ValidationError('Upload a valid image. The file you uploaded appears to be corrupted')

def get_upload_path(instance, filename):
    # Get the file extension from the optimized format or original file
    ext = instance._optimized_format if hasattr(instance, '_optimized_format') else filename.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png']:
        ext = 'jpg'
    # Generate a unique filename using UUID
    new_filename = f'{uuid.uuid4().hex[:10]}.{ext}'
    # Return the upload path
    return os.path.join('uploads', new_filename)

class Image(models.Model):
    image = models.ImageField(
        upload_to=get_upload_path,
        max_length=255,
        validators=[validate_image_file],
        help_text='Upload JPEG, PNG, or WebP images (max 10MB)'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_real = models.BooleanField(null=True)
    confidence_score = models.FloatField(null=True)
    analysis_result = models.TextField(null=True)
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(default=0)
    image_width = models.IntegerField(default=0)
    image_height = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.image:
            # Store original filename before optimization
            if not self.original_filename:
                self.original_filename = self.image.name

            # Optimize image if it's a new upload
            if not self.id:
                optimized_image, format = optimize_image(self.image)
                self._optimized_format = format
                self.image.file = optimized_image

            # Update image metadata
            self.file_size = self.image.size
            dimensions = get_image_dimensions(self.image)
            if dimensions:
                self.image_width, self.image_height = dimensions

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the image file when the model instance is deleted
        if self.image:
            try:
                storage = self.image.storage
                if storage.exists(self.image.name):
                    storage.delete(self.image.name)
            except Exception:
                pass  # Don't prevent deletion if file removal fails
        super().delete(*args, **kwargs)

    def __str__(self):
        status = self.analysis_result or 'Not analyzed'
        return f"{self.original_filename} - {status}"

    class Meta:
        ordering = ['-uploaded_at']
