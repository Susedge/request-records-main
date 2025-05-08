from django.core.management.base import BaseCommand
from django.core import management
from django.utils import timezone
import os
from onlinerequest.models import DatabaseBackup
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

class Command(BaseCommand):
    help = 'Schedule database backups every 30 days'

    def handle(self, *args, **options):
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        def create_backup():
            self.stdout.write('Creating scheduled database backup...')
            backup_file = management.call_command('backup_database')
            
            if backup_file and os.path.exists(backup_file):
                file_size = os.path.getsize(backup_file)
                DatabaseBackup.objects.create(
                    backup_file=backup_file,
                    successful=True,
                    file_size=file_size
                )
                self.stdout.write(self.style.SUCCESS('Backup completed successfully!'))
            else:
                DatabaseBackup.objects.create(
                    backup_file='',
                    successful=False,
                    file_size=0
                )
                self.stdout.write(self.style.ERROR('Backup failed!'))
        
        # Schedule job to run every 30 days
        scheduler.add_job(
            create_backup,
            'interval',
            days=30,
            id='database_backup_job',
            replace_existing=True,
        )
        
        scheduler.start()
        self.stdout.write(
            self.style.SUCCESS('Backup scheduler started. Press Ctrl+C to exit.')
        )
        
        try:
            # Keep the command running
            while True:
                pass
        except KeyboardInterrupt:
            scheduler.shutdown()
