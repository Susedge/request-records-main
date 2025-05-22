from django.contrib import admin
from django.urls import path
from onlinerequest.views import (
    views,
    register,
    login,
    dummy,
    request,
    request_user,
    record,
    codetable,
    user_approval_view,
    profile,
    reference_login,
    reports,
    admin_reports,
    qr_upload,
    user_request,
    backup_views
)

from django.conf import settings
from django.conf.urls.static import static

# Define URL paths here
urlpatterns = [
    path('admin/', admin.site.urls),

    # Main index page
    path('', views.index),

    # Student/User Records
    path('record/', record.index),
    path('record/list/', record.get_user_data),
    path('record/delete/<int:id>/', record.delete_record, name='delete_record'),
    path('admin-panel/user-records/', record.index),
    
    # Register
    path('register/', register.index),

    # Login
    path('login/', login.index),

    # Populate table
    path('dummy/', dummy.index),

    # Signup - Login with Register
    path('signup/', views.signup_view, name="signup"),
    path('send-verification-email/', register.send_verification_email, name='send_verification_email'),

    # Admin - Dashboard
    path('admin-panel/dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('admin-panel/', views.admin_dashboard, name="admin_dashboard"),

    # User - Dashboard
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user/', views.user_dashboard),

    # Request - Admin
    path('admin-panel/request/', request.index),
    path('admin-panel/user-request/', request.display_user_requests),
    path('admin-panel/user-request/<int:id>/delete', request.delete_user_request),
    path('admin-panel/user-request/<int:id>', request.display_user_request),
    path('request/list/', request.get_requests),
    path('request/<int:id>/delete/', request.delete_request),
    path('request/<int:id>/toggle-status/', request.toggle_request_status),

    # Request - User
    path('request/', request_user.index, name='request_user'),
    path('request/<int:id>/', request_user.get_request),
    path('request/active-list/', request_user.get_active_requests, name='get_active_requests'),
    # path('request/checkout/<int:id>', request_user.display_payment),
    path('get-document-description/<str:doc_code>/', request_user.get_document_description),
    path('request/user/create/', request_user.create_request),
    path('request/user/', request_user.display_user_requests),
    path('verify-document/<str:document_id>/', request_user.verify_document, name='verify_document'),
    path('request/generate-qr/<int:id>/', request_user.generate_qr, name='generate_qr'),

    # Guest - login/request
    path('reference-login/', reference_login.index),
    path('reference-login/create-request/', reference_login.create_request, name='create_request'),

    # Configuration (This is where to update code tables)
    path('codetable/', codetable.index),
    path('admin-panel/codetable/', codetable.index),
    path('codetable/edit/', codetable.edit, name='codetable_edit'),
    path('codetable/delete/', codetable.delete, name='codetable_delete'),
    path('codetable/data/', codetable.get_table_data, name='get_table_data'),
    path('codetable/check_duplicate/', codetable.check_duplicate, name='check_duplicate'),

    # User Approval
    path('admin-panel/user-accounts/', user_approval_view.index),
    path('admin-panel/user-accounts/reset-password/', user_approval_view.reset_user_password, name='reset_user_password'),

    # Logout
    path('logout/', views.logout_view, name='logout'),
    path('admin-panel/user-accounts/', user_approval_view.index),
    # Profile
    path('profile/', profile.index),

    # Reports URLs
    path('user/reports/', reports.index, name='reports'),
    path('user/reports/generate/<int:template_id>/', reports.generate_pdf, name='generate_report_pdf'),

    # Admin report URLs
    path('admin-panel/reports/', admin_reports.admin_reports, name='admin_reports'),
    path('admin-panel/reports/search-student/', admin_reports.admin_search_student, name='admin_search_student'),  # New endpoint for student search
    path('admin-panel/reports/form/<int:template_id>/', admin_reports.admin_report_form, name='admin_report_form'),
    path('admin-panel/reports/generate/<int:template_id>/', admin_reports.admin_generate_report_pdf, name='admin_generate_report_pdf'),

    # Admin Gcash upload
    path('admin-panel/qr-upload/', qr_upload.upload_qr_code, name='upload_qr_code'),

    #Analytics
    path('admin-panel/analytics/', views.request_analytics, name='request_analytics'),
    path('api/request-stats/', views.get_request_stats, name='request_stats'),
    path('api/request-details/', views.get_request_details, name='request_details'),

    path('admin-panel/user-accounts/profile/<int:user_id>/', record.get_user_profile, name='user_profile'),
    path('admin-panel/user-accounts/save-profile/', record.save_user_profile, name='save_user_profile'),
    path('profile/edit/', record.get_current_user_profile, name='edit_user_profile'),
    path('profile/save/', record.save_current_user_profile, name='save_user_profile'),

    path('admin-panel/user-request/<int:request_id>/mark-inactive', views.mark_request_inactive, name='mark_request_inactive'),
    path('request/user/authorization-letter/<int:id>/', request_user.download_authorization_letter, name='download_authorization_letter'),

    path('request/user/<int:request_id>/requirements/', user_request.get_requirements, name='get_user_request_requirements'),
    path('request/user/<int:request_id>/upload-requirements/', user_request.upload_requirements, name='upload_user_request_requirements'),
    path('request/user/<int:request_id>/check-status/', user_request.check_request_status, name='check_request_status'),
    
    path('admin-panel/user-request/<int:id>/upload-report', request.upload_report, name='upload_report'),

    # Database Backup Routes
    path('admin-panel/database-backups/', backup_views.backup_list, name='backup_list'),
    path('admin-panel/database-backups/create/', backup_views.create_backup, name='create_backup'),
    path('admin-panel/database-backups/download/<int:backup_id>/', backup_views.download_backup, name='download_backup'),
    path('admin-panel/database-backups/delete/<int:backup_id>/', backup_views.delete_backup, name='delete_backup'),
    path('admin-panel/database-backups/schedule/', backup_views.schedule_backup, name='schedule_backup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
