import os
import time
import datetime
import shutil
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

class Command(BaseCommand):
    help = 'Backup database to a specified directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            default=None,
            help='Directory where backups will be stored',
        )

    def handle(self, *args, **options):
        # Set default backup directory if not provided
        output_dir = options['output_dir'] or os.path.join(settings.BASE_DIR, 'backups')
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Get current timestamp for the filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        # Detect database engine and create appropriate backup
        db_settings = settings.DATABASES['default']
        db_engine = db_settings['ENGINE']
        
        if 'sqlite3' in db_engine:
            # SQLite backup
            db_path = db_settings['NAME']
            backup_file = os.path.join(output_dir, f'db_backup_{timestamp}.sqlite3')
            
            try:
                shutil.copy2(db_path, backup_file)
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully backed up SQLite database to {backup_file}'
                ))
                return backup_file
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Backup failed: {str(e)}'))
                return None
                
        elif 'mysql' in db_engine:
            # MySQL backup
            backup_file = os.path.join(output_dir, f'db_backup_{timestamp}.sql')
            
            cmd = [
                'mysqldump',
                '--user={}'.format(db_settings['USER']),
                '--password={}'.format(db_settings['PASSWORD']),
                '--host={}'.format(db_settings.get('HOST', 'localhost')),
                '--port={}'.format(db_settings.get('PORT', '3306')),
                db_settings['NAME'],
                '-r', backup_file
            ]
            
            try:
                subprocess.run(cmd, check=True)
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully backed up MySQL database to {backup_file}'
                ))
                return backup_file
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Backup failed: {str(e)}'))
                return None
        
        else:
            self.stdout.write(self.style.ERROR(
                f'Unsupported database engine: {db_engine}'
            ))
            return None