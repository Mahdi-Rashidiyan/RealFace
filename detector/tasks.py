from django.core.management import call_command
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import threading
import time
import logging
import os
import datetime
from django.core.management.base import BaseCommand
from django.db.models import Q
import gc

logger = logging.getLogger(__name__)

class TaskStatus:
    """Task status tracker"""
    def __init__(self, task_name):
        self.task_name = task_name
        self.cache_key_running = f'task_running_{task_name}'
        self.cache_key_last_run = f'last_run_{task_name}'
        self.cache_key_last_status = f'last_status_{task_name}'
        self.cache_key_error = f'last_error_{task_name}'

    def start(self):
        """Mark task as started"""
        cache.set(self.cache_key_running, True, timeout=3600)
        cache.set(self.cache_key_last_run, timezone.now(), timeout=86400)
        cache.delete(self.cache_key_error)
        logger.info(f'Task {self.task_name} started')

    def complete(self, success=True, error=None):
        """Mark task as completed"""
        cache.delete(self.cache_key_running)
        cache.set(self.cache_key_last_status, success, timeout=86400)
        if error:
            cache.set(self.cache_key_error, str(error), timeout=86400)
            logger.error(f'Task {self.task_name} failed: {error}')
        else:
            logger.info(f'Task {self.task_name} completed successfully')

    @property
    def is_running(self):
        """Check if task is currently running"""
        return bool(cache.get(self.cache_key_running))

    @property
    def last_run(self):
        """Get last run timestamp"""
        return cache.get(self.cache_key_last_run)

    @property
    def last_status(self):
        """Get last run status"""
        return cache.get(self.cache_key_last_status)

    @property
    def last_error(self):
        """Get last error message"""
        return cache.get(self.cache_key_error)

class BackgroundTasks:
    """Background task manager"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BackgroundTasks, cls).__new__(cls)
                cls._instance.cleanup_thread = None
                cls._instance.backup_thread = None
                cls._instance.stop_event = threading.Event()
                cls._instance.cleanup_status = TaskStatus('cleanup')
                cls._instance.backup_status = TaskStatus('backup')
            return cls._instance

    def start(self):
        """Start all background tasks"""
        self.stop_event.clear()
        self._start_cleanup_task()
        self._start_backup_task()
        logger.info("Background tasks started")

    def stop(self):
        """Stop all background tasks"""
        if self.cleanup_thread or self.backup_thread:
            self.stop_event.set()
            if self.cleanup_thread:
                self.cleanup_thread.join()
            if self.backup_thread:
                self.backup_thread.join()
            self.cleanup_status.complete()
            self.backup_status.complete()
            logger.info("Background tasks stopped")

    def _start_cleanup_task(self):
        """Start the cleanup task in a separate thread"""
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            self.cleanup_thread = threading.Thread(target=self._run_cleanup, daemon=True)
            self.cleanup_thread.start()

    def _start_backup_task(self):
        """Start the backup task in a separate thread"""
        if self.backup_thread is None or not self.backup_thread.is_alive():
            self.backup_thread = threading.Thread(target=self._run_backup, daemon=True)
            self.backup_thread.start()

    def _run_cleanup(self):
        """Run the cleanup task periodically"""
        cleanup_logger = logging.getLogger('detector.tasks.cleanup')
        
        while not self.stop_event.is_set():
            try:
                self.cleanup_status.start()
                
                max_age = getattr(settings, 'IMAGE_CLEANUP', {}).get('MAX_AGE_DAYS', 7)
                analyzed_only = getattr(settings, 'IMAGE_CLEANUP', {}).get('ANALYZED_ONLY', True)
                
                cleanup_logger.info(f'Running cleanup (max age: {max_age} days, analyzed only: {analyzed_only})')
                call_command('cleanup_old_images', days=max_age, analyzed_only=analyzed_only)
                
                self.cleanup_status.complete(success=True)
                
                # Sleep for 24 hours
                for _ in range(24 * 60):  # 24 hours * 60 minutes
                    if self.stop_event.is_set():
                        break
                    time.sleep(60)  # Check every minute if we should stop
                    
            except Exception as e:
                error_msg = f"Error in cleanup task: {str(e)}"
                cleanup_logger.error(error_msg)
                self.cleanup_status.complete(success=False, error=error_msg)
                time.sleep(300)  # Sleep for 5 minutes on error

    def _run_backup(self):
        """Run the backup task periodically"""
        backup_logger = logging.getLogger('detector.tasks.backup')
        
        while not self.stop_event.is_set():
            try:
                # Only run backup at midnight
                current_hour = timezone.localtime().hour
                if current_hour == 0:
                    self.backup_status.start()
                    
                    backup_logger.info('Starting database and media backup')
                    call_command('backup_db', include_media=True)
                    
                    self.backup_status.complete(success=True)
                    
                    # Sleep until next check (1 hour to avoid multiple backups)
                    time.sleep(3600)
                else:
                    # Check every 30 minutes
                    time.sleep(1800)
                    
            except Exception as e:
                error_msg = f"Error in backup task: {str(e)}"
                backup_logger.error(error_msg)
                self.backup_status.complete(success=False, error=error_msg)
                time.sleep(300)  # Sleep for 5 minutes on error

    def get_tasks_status(self):
        """Get status of all background tasks"""
        return {
            'cleanup': {
                'running': self.cleanup_status.is_running,
                'last_run': self.cleanup_status.last_run,
                'last_status': self.cleanup_status.last_status,
                'last_error': self.cleanup_status.last_error,
            },
            'backup': {
                'running': self.backup_status.is_running,
                'last_run': self.backup_status.last_run,
                'last_status': self.backup_status.last_status,
                'last_error': self.backup_status.last_error,
            }
        }

background_tasks = BackgroundTasks()

def cleanup_old_images(days=7):
    """
    Clean up images older than specified days to free up storage space
    """
    from .models import Image
    
    try:
        # Get date threshold
        threshold_date = timezone.now() - datetime.timedelta(days=days)
        
        # Find old images that have been analyzed
        old_images = Image.objects.filter(
            uploaded_at__lt=threshold_date,
            analysis_result__isnull=False
        )
        
        # Delete them
        count = old_images.count()
        if count > 0:
            for img in old_images:
                img.delete()
            logger.info(f"Successfully deleted {count} images older than {days} days (analyzed only)")
        else:
            logger.info(f"No images older than {days} days to delete")
            
        # Force garbage collection
        gc.collect()
            
        return count
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return 0
        
def cleanup_unanalyzed_images(hours=24):
    """
    Clean up unanalyzed images older than specified hours
    """
    from .models import Image
    
    try:
        # Get date threshold
        threshold_date = timezone.now() - datetime.timedelta(hours=hours)
        
        # Find old unanalyzed images
        old_unanalyzed = Image.objects.filter(
            uploaded_at__lt=threshold_date,
            analysis_result__isnull=True
        )
        
        # Delete them
        count = old_unanalyzed.count()
        if count > 0:
            for img in old_unanalyzed:
                img.delete()
            logger.info(f"Successfully deleted {count} unanalyzed images older than {hours} hours")
        else:
            logger.info(f"No unanalyzed images older than {hours} hours to delete")
            
        # Force garbage collection
        gc.collect()
            
        return count
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return 0

class Command(BaseCommand):
    """
    Management command to clean up old images
    """
    help = 'Clean up old images to free up storage'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days', 
            type=int, 
            default=7,
            help='Delete analyzed images older than this many days'
        )
        parser.add_argument(
            '--hours', 
            type=int, 
            default=24,
            help='Delete unanalyzed images older than this many hours'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        hours = options['hours']
        
        try:
            count1 = cleanup_old_images(days)
            count2 = cleanup_unanalyzed_images(hours)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count1} analyzed images older than {days} days')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count2} unanalyzed images older than {hours} hours')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error: {str(e)}')
            )