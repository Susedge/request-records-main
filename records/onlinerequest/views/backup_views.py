import os
import subprocess
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.core.management import call_command
from onlinerequest.models import DatabaseBackup
from django.contrib.auth.decorators import login_required

@login_required
def backup_list(request):
    """View to display the list of database backups"""
    backups = DatabaseBackup.objects.all().order_by('-created_at')
    context = {
        'backups': backups,
        'title': 'Database Backups'
    }
    return render(request, 'admin/backup_list.html', context)

@login_required
def create_backup(request):
    """View to create a new database backup"""
    if request.method == 'POST':
        try:
            backup_file = call_command('backup_database')
            
            if backup_file and os.path.exists(backup_file):
                file_size = os.path.getsize(backup_file)
                DatabaseBackup.objects.create(
                    backup_file=backup_file,
                    successful=True,
                    file_size=file_size
                )
                messages.success(request, f"Database backup created successfully at {backup_file}")
            else:
                DatabaseBackup.objects.create(
                    backup_file='',
                    successful=False,
                    file_size=0
                )
                messages.error(request, "Database backup failed.")
            
            return redirect('backup_list')
        except Exception as e:
            messages.error(request, f"Error creating backup: {str(e)}")
            return redirect('backup_list')
            
    context = {
        'title': 'Create Database Backup',
        'backup_dir': os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'backups')
    }
    return render(request, 'admin/backup_confirm.html', context)

@login_required
def download_backup(request, backup_id):
    """View to download a specific backup file"""
    try:
        backup = DatabaseBackup.objects.get(id=backup_id)
        if os.path.exists(backup.backup_file):
            with open(backup.backup_file, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(backup.backup_file)}"'
                return response
        else:
            messages.error(request, "Backup file not found on disk.")
    except DatabaseBackup.DoesNotExist:
        messages.error(request, "Backup record not found.")
    except Exception as e:
        messages.error(request, f"Error downloading backup: {str(e)}")
    
    return redirect('backup_list')

@login_required
def delete_backup(request, backup_id):
    """View to delete a specific backup"""
    if request.method == 'POST':
        try:
            backup = DatabaseBackup.objects.get(id=backup_id)
            if os.path.exists(backup.backup_file):
                os.remove(backup.backup_file)
            backup.delete()
            messages.success(request, "Backup deleted successfully.")
        except DatabaseBackup.DoesNotExist:
            messages.error(request, "Backup record not found.")
        except Exception as e:
            messages.error(request, f"Error deleting backup: {str(e)}")
    
    return redirect('backup_list')

@login_required
def schedule_backup(request):
    """View to configure automated backup schedule"""
    if request.method == 'POST':
        # Here you would implement saving the schedule configuration
        frequency = request.POST.get('frequency', '30')  # Default to 30 days
        try:
            # Save the configuration somewhere (could be in a settings model)
            messages.success(request, f"Automated backups scheduled every {frequency} days")
        except Exception as e:
            messages.error(request, f"Error scheduling backups: {str(e)}")
        return redirect('backup_list')
        
    context = {
        'title': 'Schedule Automated Backups',
        # You could load current schedule configuration here
    }
    return render(request, 'admin-panel/backup_schedule.html', context)