from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from detector.models import Image
import datetime
import os

class Command(BaseCommand):
    help = 'Cleanup old analyzed images to free up storage space'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete images older than specified days'
        )
        parser.add_argument(
            '--analyzed-only',
            action='store_true',
            help='Only delete images that have been analyzed'
        )

    def handle(self, *args, **options):
        days = options['days']
        analyzed_only = options['analyzed_only']
        cutoff_date = timezone.now() - datetime.timedelta(days=days)
        
        # Build query
        query = Image.objects.filter(uploaded_at__lt=cutoff_date)
        if analyzed_only:
            query = query.exclude(analysis_result__isnull=True)
        
        # Get count before deletion
        total_count = query.count()
        
        # Delete images and their files
        deleted_count = 0
        failed_count = 0
        
        for image in query:
            try:
                # The delete() method will handle file deletion through our model's delete() method
                image.delete()
                deleted_count += 1
            except Exception as e:
                failed_count += 1
                self.stderr.write(f"Failed to delete image {image.id}: {str(e)}")
        
        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {deleted_count} images older than {days} days'
                f'{" (analyzed only)" if analyzed_only else ""}'
            )
        )
        
        if failed_count:
            self.stderr.write(
                self.style.WARNING(f'Failed to delete {failed_count} images')
            )