from django.urls import path
from . import views as request
from . import views as document

urlpatterns = [
    path('request/<int:id>/delete/', request.delete_request),
    path('request/<int:id>/toggle-status/', request.toggle_request_status),
    path('document/<str:code>/delete/', document.delete_document),
] 