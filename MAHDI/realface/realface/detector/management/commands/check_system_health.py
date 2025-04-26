from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import os
import psutil
import json
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Check system health and background task status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (text or json)'
        )

    def handle(self, *args, **options):
        health_info = self._check_health()
        
        if options['format'] == 'json':
            self.stdout.write(json.dumps(health_info))
        else:
            self._display_health_info(health_info)
        
        # Store health info in cache for dashboard access
        cache.set('system_health', health_info, timeout=300)  # Cache for 5 minutes

    def _check_health(self):
        """Gather system health information"""
        process = psutil.Process()
        
        # Check disk usage for media and backup directories
        media_usage = self._get_directory_size(settings.MEDIA_ROOT)
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        backup_usage = self._get_directory_size(backup_dir) if os.path.exists(backup_dir) else 0
        
        # Get latest backup info
        latest_backup = self._get_latest_backup_info(backup_dir)
        
        return {
            'timestamp': timezone.now().isoformat(),
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': process.memory_percent(),
                'disk_usage': {
                    'media': self._format_size(media_usage),
                    'backups': self._format_size(backup_usage),
                },
                'uptime': self._get_uptime(),
            },
            'background_tasks': {
                'cleanup_task': self._check_task_status('cleanup'),
                'backup_task': self._check_task_status('backup'),
            },
            'latest_backup': latest_backup,
            'cache_status': self._check_cache_status(),
        }

    def _get_directory_size(self, path):
        """Calculate total size of a directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def _format_size(self, size):
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _get_uptime(self):
        """Get system uptime"""
        try:
            return str(timedelta(seconds=int(psutil.boot_time())))
        except Exception:
            return "Unknown"

    def _check_task_status(self, task_name):
        """Check if a background task is running"""
        last_run = cache.get(f'last_run_{task_name}')
        is_running = cache.get(f'task_running_{task_name}')
        
        if last_run:
            # Convert datetime to ISO format string for JSON serialization
            last_run = last_run.isoformat()
        
        return {
            'running': bool(is_running),
            'last_run': last_run,
        }

    def _get_latest_backup_info(self, backup_dir):
        """Get information about the latest backup"""
        if not os.path.exists(backup_dir):
            return None
            
        backup_files = []
        for f in os.listdir(backup_dir):
            if f.startswith('db_backup_'):
                path = os.path.join(backup_dir, f)
                backup_files.append({
                    'file': f,
                    'time': datetime.fromtimestamp(os.path.getmtime(path)),
                    'size': os.path.getsize(path),
                })
        
        if not backup_files:
            return None
            
        latest = max(backup_files, key=lambda x: x['time'])
        return {
            'filename': latest['file'],
            'timestamp': latest['time'].isoformat(),
            'size': self._format_size(latest['size']),
        }

    def _check_cache_status(self):
        """Check if cache is working"""
        try:
            test_key = 'health_check_test'
            cache.set(test_key, 'test', 10)
            result = cache.get(test_key) == 'test'
            cache.delete(test_key)
            return {
                'working': result,
                'backend': settings.CACHES['default']['BACKEND'],
            }
        except Exception as e:
            return {
                'working': False,
                'error': str(e),
                'backend': settings.CACHES['default']['BACKEND'],
            }

    def _display_health_info(self, health_info):
        """Display health information in a readable format"""
        self.stdout.write('\n=== System Health Report ===\n')
        
        # System info
        self.stdout.write(self.style.MIGRATE_HEADING('\nSystem Information:'))
        system = health_info['system']
        self.stdout.write(f"CPU Usage: {system['cpu_percent']}%")
        self.stdout.write(f"Memory Usage: {system['memory_percent']:.1f}%")
        self.stdout.write(f"Uptime: {system['uptime']}")
        
        # Disk usage
        self.stdout.write(self.style.MIGRATE_HEADING('\nDisk Usage:'))
        disk = system['disk_usage']
        self.stdout.write(f"Media Directory: {disk['media']}")
        self.stdout.write(f"Backups Directory: {disk['backups']}")
        
        # Background tasks
        self.stdout.write(self.style.MIGRATE_HEADING('\nBackground Tasks:'))
        tasks = health_info['background_tasks']
        for task_name, status in tasks.items():
            running = 'Running' if status['running'] else 'Stopped'
            last_run = status['last_run'] or 'Never'
            self.stdout.write(f"{task_name.title()}: {running} (Last run: {last_run})")
        
        # Latest backup
        self.stdout.write(self.style.MIGRATE_HEADING('\nLatest Backup:'))
        if health_info['latest_backup']:
            backup = health_info['latest_backup']
            self.stdout.write(f"File: {backup['filename']}")
            self.stdout.write(f"Time: {backup['timestamp']}")
            self.stdout.write(f"Size: {backup['size']}")
        else:
            self.stdout.write('No backups found')
        
        # Cache status
        self.stdout.write(self.style.MIGRATE_HEADING('\nCache Status:'))
        cache_status = health_info['cache_status']
        status = 'Working' if cache_status['working'] else 'Not Working'
        self.stdout.write(f"Status: {status}")
        self.stdout.write(f"Backend: {cache_status['backend']}")
        
        self.stdout.write('\n')