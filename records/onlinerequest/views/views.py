from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import logout
from django.shortcuts import redirect
from onlinerequest.models import Request, Requirement, User_Request, Profile, Document
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

def index(request):
    request_forms = Request.objects.all()
    for request_form in request_forms:
        requirement_descriptions = []
        for requirement_code in request_form.files_required.split(','):
            try:
                requirement = Requirement.objects.get(code=requirement_code)
                requirement_descriptions.append(requirement.description)
            except Requirement.DoesNotExist:
                requirement_descriptions.append(requirement_code)
        request_form.requirement_descriptions = requirement_descriptions

    return render(request, 'index.html', {'request_forms': request_forms})

def signup_view(request):
    return render(request, 'signup.html')

def admin_dashboard(request):
    return render (request, "admin/dashboard.html")

def user_dashboard(request):
    return render (request, "user/dashboard.html")

def logout_view(request):
    logout(request)
    return redirect('/signup/')

def user_reports(request):
    user_records = User_Request.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user/reports.html', {'user_records': user_records})

# Analytics
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import ExtractDay, ExtractHour

def request_analytics(request):
    return render(request, 'admin/analytics.html')

def get_request_stats(request):
    filter_type = request.GET.get('filter', 'week')
    
    # Date filtering
    now = timezone.now()
    if filter_type == 'day':
        start_date = now - timedelta(days=1)
    elif filter_type == 'week':
        start_date = now - timedelta(weeks=1)
    else:  # month
        start_date = now - timedelta(days=30)
        
    # Get requests within date range
    requests = User_Request.objects.filter(created_at__gte=start_date)
    
    # Most requested documents
    doc_stats = requests.values('request__document__description')\
                       .annotate(count=Count('id'))\
                       .order_by('-count')
    
    # Processing time stats
    completed_requests = requests.filter(status='Completed')
    processing_times = []
    
    for req in completed_requests:
        time_diff = req.updated_at - req.created_at
        days = time_diff.days
        hours = time_diff.seconds // 3600
        status = 'Completed'
        
        if time_diff > timedelta(days=3):
            status = 'late'
            
        processing_times.append({
            'request_id': req.id,
            'days': days,
            'hours': hours,
            'status': status
        })

    return JsonResponse({
        'total_requests': requests.count(),
        'document_stats': list(doc_stats),
        'processing_times': processing_times
    })

# Add to your existing imports at the top
from django.db.models import F
from django.utils.timesince import timesince

# Add this optimized version of the get_request_details endpoint
def get_request_details(request):
    # Get all user requests with optimized querying
    user_requests = User_Request.objects.select_related(
        'user', 'request', 'request__document'
    ).prefetch_related(
        'user__profile'
    ).order_by('-created_at')
    
    # Limit to 1000 most recent requests to avoid performance issues
    user_requests = user_requests[:1000]
    
    # Prepare data for DataTable
    data = []
    for req in user_requests:
        # Calculate processing time
        processing_time = ""
        date_completed = ""
        
        if req.status == "Completed":
            date_completed = req.updated_at.strftime('%b %d, %Y')
            
            # Calculate processing time more efficiently
            processing_time = timesince(req.created_at, req.updated_at)
        
        # Get profile information if available
        try:
            profile = req.user.profile
            name = f"{profile.first_name} {profile.middle_name} {profile.last_name}".strip()
            contact = profile.contact_no
        except (Profile.DoesNotExist, AttributeError):
            name = req.user.student_number
            contact = "N/A"
        
        # Format schedule and date_release
        schedule = req.schedule.strftime('%b %d, %Y %I:%M %p') if req.schedule else "N/A"
        date_released = req.date_release.strftime('%b %d, %Y') if req.date_release else "N/A"
        
        # Add request to data with optimized structure
        data.append({
            'reference_number': f"REQ-{req.id:06d}",
            'date_requested': req.created_at.strftime('%b %d, %Y'),
            'client_type': req.user.get_user_type_display(),
            'requested_by': name,
            'contact_details': contact,
            'email': req.user.email,
            'service_type': req.request.document.description if req.request and req.request.document else "N/A",
            'purpose': req.purpose or "N/A",
            'status': req.status,
            'schedule': schedule,
            'date_completed': date_completed,
            'date_released': date_released,
            'processing_time': processing_time
        })
    
    return JsonResponse(data, safe=False)

def mark_request_inactive(request, request_id):
    try:
        user_request = User_Request.objects.get(id=request_id)
        user_request.status = "inactive"
        user_request.save()
        
        return JsonResponse({
            'status': True,
            'message': 'Request marked as inactive successfully'
        })
    except User_Request.DoesNotExist:
        return JsonResponse({
            'status': False,
            'message': 'Request not found'
        })
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': f'Error: {str(e)}'
        })

def admin_user_requests(request):
    # Use select_related to efficiently fetch related Profile data
    user_requests = User_Request.objects.all().select_related('user', 'user__profile', 'request', 'request__document')
    
    # Get document types for the filter dropdown - temporarily remove active filter
    document_types = Document.objects.all().order_by('description')
    
    # Debug: print all documents
    all_docs = Document.objects.all()
    print(f"All documents: {all_docs.count()}")
    for doc in all_docs:
        print(f"Document: {doc.id} - {doc.code} - {doc.description} - Active: {doc.active if hasattr(doc, 'active') else 'N/A'}")
    
    # Check for requests whose last update was more than a year ago
    one_year_ago = timezone.now() - timedelta(days=365)
    old_requests = User_Request.objects.filter(
        updated_at__lt=one_year_ago,
        status__ne="inactive"
    )
    
    # Update old requests to inactive
    updated_count = 0
    for old_request in old_requests:
        old_request.status = "inactive"
        old_request.save()
        updated_count += 1
    
    if updated_count > 0:
        messages.info(request, f"{updated_count} requests not updated in over a year were automatically marked as inactive.")
    
    context = {
        'user_requests': user_requests,
        'document_types': document_types,
    }
    
    return render(request, 'admin/request/user-request.html', context)
