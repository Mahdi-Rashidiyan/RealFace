from django.apps import AppConfig
import sys

class DetectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'detector'

    def ready(self):
        # Avoid running background tasks in manage.py commands except runserver
        if 'runserver' not in sys.argv:
            return

        # Start all background tasks
        from .tasks import background_tasks
        background_tasks.start()
