import os
import datetime
from django.core.management.base import BaseCommand
from django.core import management
from django.utils import timezone
from onlinerequest.models import DatabaseBackup

class Command(BaseCommand):
    help = 'Run scheduled database backup if needed'

    def handle(self, *args, **options):
        # Check if a backup is due (now running daily)
        latest_backup = DatabaseBackup.objects.filter(successful=True).order_by('-created_at').first()
        days_since_last_backup = 1  # Default
        
        if latest_backup:
            days_since_last_backup = (timezone.now() - latest_backup.created_at).days
        
        if days_since_last_backup >= 1:  # Backup every day
            self.stdout.write('Running scheduled database backup...')
            
            # Call the backup command
            backup_file = management.call_command('backup_database', verbosity=0)
            
            # Log the backup result in our model
            if backup_file and os.path.exists(backup_file):
                file_size = os.path.getsize(backup_file)
                DatabaseBackup.objects.create(
                    backup_file=backup_file,
                    successful=True,
                    file_size=file_size
                )
                self.stdout.write(self.style.SUCCESS('Scheduled backup completed successfully!'))
            else:
                DatabaseBackup.objects.create(
                    backup_file='',
                    successful=False,
                    file_size=0
                )
                self.stdout.write(self.style.ERROR('Scheduled backup failed!'))
        else:
            self.stdout.write(f'No backup needed yet. Next backup in {1 - days_since_last_backup} days.')