import os
import time
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import management

class Command(BaseCommand):
    help = 'Create a backup of the database and media files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--include-media',
            action='store_true',
            help='Include media files in the backup'
        )

    def handle(self, *args, **options):
        # Create backups directory if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Generate timestamp for backup files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Backup database
        db_backup_path = os.path.join(backup_dir, f'db_backup_{timestamp}.json')
        try:
            management.call_command('dumpdata', 
                                 exclude=['contenttypes', 'auth.permission'],
                                 natural_foreign=True,
                                 natural_primary=True,
                                 output=db_backup_path,
                                 indent=2)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created database backup: {db_backup_path}')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error creating database backup: {str(e)}')
            )
            return

        # Backup media files if requested
        if options['include_media']:
            media_backup_path = os.path.join(backup_dir, f'media_backup_{timestamp}')
            try:
                shutil.copytree(settings.MEDIA_ROOT, media_backup_path)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully backed up media files: {media_backup_path}')
                )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f'Error backing up media files: {str(e)}')
                )

        # Clean up old backups (keep last 5)
        self._cleanup_old_backups(backup_dir)

    def _cleanup_old_backups(self, backup_dir):
        """Keep only the 5 most recent backups of each type"""
        db_backups = []
        media_backups = []

        for item in os.listdir(backup_dir):
            if item.startswith('db_backup_'):
                db_backups.append(os.path.join(backup_dir, item))
            elif item.startswith('media_backup_'):
                media_backups.append(os.path.join(backup_dir, item))

        # Sort by modification time (newest first)
        db_backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        media_backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        # Remove old backups
        for old_backup in db_backups[5:]:
            try:
                os.remove(old_backup)
                self.stdout.write(f'Removed old database backup: {old_backup}')
            except Exception as e:
                self.stderr.write(f'Error removing old backup {old_backup}: {str(e)}')

        for old_backup in media_backups[5:]:
            try:
                shutil.rmtree(old_backup)
                self.stdout.write(f'Removed old media backup: {old_backup}')
            except Exception as e:
                self.stderr.write(f'Error removing old backup {old_backup}: {str(e)}')