from django.contrib import admin
from django.core.management import call_command
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django.template.response import TemplateResponse
import os
from .models import (Record, Course, Requirement, Code, User, Profile, 
                     RegisterRequest, Document, Request, User_Request, 
                     Purpose, ReportTemplate, TempRecord, DatabaseBackup)

# Register your general models
admin.site.register(Record)
admin.site.register(Course)
admin.site.register(Requirement)
admin.site.register(Code)
admin.site.register(Profile)
admin.site.register(RegisterRequest)
admin.site.register(Document)
admin.site.register(Request)
admin.site.register(Purpose)
admin.site.register(ReportTemplate)
admin.site.register(TempRecord)
admin.site.register(User)

@admin.register(DatabaseBackup)
class DatabaseBackupAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'successful', 'get_file_size_display', 'backup_file']
    list_filter = ['successful', 'created_at']
    actions = ['delete_selected']
    readonly_fields = ['created_at', 'successful', 'file_size', 'backup_file']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('backup-now/', self.admin_site.admin_view(self.backup_now_view), name='backup-now'),
        ]
        return custom_urls + urls
    
    def backup_now_view(self, request):
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
                
                return redirect('admin:onlinerequest_databasebackup_changelist')
            except Exception as e:
                messages.error(request, f"Error creating backup: {str(e)}")
                return redirect('admin:onlinerequest_databasebackup_changelist')
                
        # Use our custom template instead of the simple admin template
        context = {
            'title': 'Database Backup',
            'opts': self.model._meta,
            'backup_dir': os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'backups')
        }
        return TemplateResponse(request, 'admin/backup_dashboard.html', context)
    
    def has_add_permission(self, request):
        return False
