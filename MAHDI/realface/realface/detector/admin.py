from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.core.cache import cache
from django.conf import settings
import datetime
import psutil
import os
from .models import Image
from .tasks import background_tasks

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'original_filename', 'analysis_result', 'confidence_score', 
                   'file_size_display', 'dimensions_display', 'uploaded_at')
    list_filter = ('is_real', 'uploaded_at')
    search_fields = ('original_filename', 'analysis_result')
    readonly_fields = ('image_preview', 'file_size_display', 'dimensions_display', 
                      'uploaded_at', 'confidence_score')
    fieldsets = (
        ('Image Information', {
            'fields': ('image_preview', 'image', 'original_filename')
        }),
        ('Analysis Results', {
            'fields': ('is_real', 'confidence_score', 'analysis_result')
        }),
        ('Technical Details', {
            'fields': ('file_size_display', 'dimensions_display', 'uploaded_at')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', 
                 self.admin_site.admin_view(self.dashboard_view), 
                 name='system_dashboard'),
            path('system-health/',
                 self.admin_site.admin_view(self.system_health),
                 name='system_health'),
            path('task-status/',
                 self.admin_site.admin_view(self.task_status),
                 name='task_status'),
        ]
        return custom_urls + urls

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', 
                             obj.image.url)
        return "No image"
    thumbnail.short_description = 'Thumbnail'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 300px; max-width: 100%;" />', 
                             obj.image.url)
        return "No image"
    image_preview.short_description = 'Image Preview'

    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} bytes"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size/1024:.1f} KB"
        else:
            return f"{obj.file_size/(1024*1024):.1f} MB"
    file_size_display.short_description = 'File Size'

    def dimensions_display(self, obj):
        if obj.image_width and obj.image_height:
            return f"{obj.image_width} × {obj.image_height}"
        return "Unknown"
    dimensions_display.short_description = 'Dimensions'

    def dashboard_view(self, request):
        """Render the system dashboard"""
        context = dict(
            self.admin_site.each_context(request),
            title="System Dashboard"
        )
        return TemplateResponse(
            request, 
            "admin/detector/dashboard.html",
            context
        )

    def system_health(self, request):
        """Get system health information"""
        process = psutil.Process()
        
        try:
            media_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(settings.MEDIA_ROOT)
                for filename in filenames
            )
        except Exception:
            media_size = 0
            
        try:
            backup_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(settings.BASE_DIR / 'backups')
                for filename in filenames
            )
        except Exception:
            backup_size = 0

        return JsonResponse({
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': process.memory_percent(),
                'disk_usage': {
                    'media': self._format_size(media_size),
                    'backups': self._format_size(backup_size),
                },
                'uptime': str(datetime.timedelta(seconds=int(psutil.boot_time())))
            },
            'cache': {
                'backend': settings.CACHES['default']['BACKEND'],
                'status': self._check_cache_status()
            }
        })

    def task_status(self, request):
        """Get background tasks status"""
        return JsonResponse(background_tasks.get_tasks_status())

    def _format_size(self, size):
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _check_cache_status(self):
        """Check if cache is working"""
        try:
            key = 'admin_cache_check'
            cache.set(key, True, 10)
            result = cache.get(key)
            cache.delete(key)
            return result is True
        except Exception:
            return False

    class Media:
        css = {
            'all': ('detector/css/admin.css',)
        }
        js = ('detector/js/admin-dashboard.js',)
