from django.apps import AppConfig
import os
from django.conf import settings

class OnlinerequestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'onlinerequest'
    
    def ready(self):
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
