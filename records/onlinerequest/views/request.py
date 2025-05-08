from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from ..models import Document
from ..models import Request
from ..models import Requirement
from ..models import User_Request
from ..serializers import RequestSerializer
from django.conf import settings
import os

def index(request):
    if request.method == "POST":
        post_document = request.POST.get("documents")
        post_files_required = request.POST.get("requirements")
        post_description = request.POST.get("description")
        post_price = request.POST.get("price")

        document = Document.objects.get(code = post_document)
        created_request = Request.objects.create(document=document, price=post_price, files_required=post_files_required, description=post_description)
        
        if created_request:
            return JsonResponse({"status": True, "message": "Request Created"})
        else:
            return JsonResponse({"status": False, "message": "Request not created. Please try again."})
    else:
        documents = Document.objects.all()
        requirements = Requirement.objects.all()
        return render(request, 'admin/request/index.html', {'documents': documents, 'requirements': requirements})

def display_user_requests(request):    
    user_requests = User_Request.objects.all()
    return render(request, 'admin/request/user-request.html', {'user_requests': user_requests })

def display_user_request(request, id):
    if request.method == "POST":
        new_status = request.POST.get('new_status')
        requested_file = request.FILES.get('requested_file')
        processing_time = request.POST.get("processing_time")
        pickup_schedule = request.POST.get("pickupSchedule")
        date_release = request.POST.get("dateRelease")
        remarks = request.POST.get("remarks")
        action = request.POST.get("action")  # New parameter to track actions like approve/decline
        
        user_request = User_Request.objects.get(id=id)

        # Set approved flag based on action
        if request.POST.get('approved') == 'true' or action == 'approve':
            user_request.approved = True
        
        # Handle uploading requested file if provided
        if requested_file is not None:
            encrypted_file_path = handle_uploaded_file(id, requested_file)
            user_request.requested = encrypted_file_path

        # Update request status
        user_request.status = new_status
        
        # Add remarks if provided
        if remarks:
            user_request.remarks = remarks  # Assuming you have a remarks field
        
        # Handle schedule and release date
        if pickup_schedule:
            from django.utils.dateparse import parse_datetime
            user_request.schedule = parse_datetime(pickup_schedule)
        
        if date_release:
            from django.utils.dateparse import parse_datetime
            user_request.date_release = parse_datetime(date_release)
        elif processing_time:
            # Set a dynamic attribute for the calculate_date_release method
            user_request.processing_time = processing_time
            user_request.date_release = user_request.calculate_date_release()
        
        user_request.save()

        return JsonResponse({
            'status': True, 
            'message': 'Request updated successfully.', 
            'request_status': user_request.status
        })
        
    if request.method == "GET":
        try:
            user_request = User_Request.objects.get(id=id)
            uploads = []
            
            # Get all requirements for the form
            document_requirements = Requirement.objects.all()
            
            # Process uploads for display
            if user_request.uploads:
                key = generate_key_from_user(id)
                upload_items = user_request.uploads.split(',')
                for user_request_upload in upload_items:
                    if user_request_upload.strip():
                        upload = user_request_upload.replace("<", "").replace(">", "").split('&')
                        # First decrypt the encrypted hash
                        decrypted_hash = decrypt_data(upload[1], key)
                    
                        # Reconstruct original file path
                        base_path = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(id))
                    
                        # Check if base path exists
                        if os.path.exists(base_path):
                            for filename in os.listdir(base_path):
                                file_path = os.path.join(base_path, filename)
                                current_hash = hashlib.sha256(file_path.encode()).hexdigest()
                                if current_hash == decrypted_hash:
                                    uploads.append({
                                        'code': getCodeDescription(Requirement, upload[0]),
                                        'path': file_path
                                    })
                                    break

            return render(request, 'admin/request/view-user-request.html', {
                'user_request': user_request,
                'uploads': uploads,
                'document_requirements': document_requirements,
            })
        except User_Request.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'User request not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': False, 'message': f'Error: {str(e)}'}, status=500)

# Add a new function to upload report files
def upload_report(request, id):
    if request.method == "POST":
        new_status = request.POST.get('new_status')
        requested_file = request.FILES.get('requested_file')
        date_release = request.POST.get("dateRelease")
        
        user_request = User_Request.objects.get(id=id)
        
        # Handle file upload if provided
        file_path = None
        if requested_file:
            encrypted_file_path = handle_uploaded_file(id, requested_file)
            user_request.requested = encrypted_file_path
            file_path = os.path.join("/static/user_request", str(id), "approved", requested_file.name)
        
        # Handle date release
        if date_release:
            from django.utils.dateparse import parse_datetime
            user_request.date_release = parse_datetime(date_release)
        
        # Update status if changed
        if new_status:
            user_request.status = new_status
        
        user_request.save()
        
        return JsonResponse({
            'status': True,
            'message': 'Report uploaded successfully.',
            'request_status': user_request.status,
            'file_path': file_path
        })
    
    return JsonResponse({'status': False, 'message': 'Invalid request method'}, status=400)

def getCodeDescription(model, key):
    try:
        model_instance = model.objects.get(code=key)
        return model_instance.description
    except model.DoesNotExist:
        return f"Unknown requirement ({key})"

def delete_user_request(request, id):
    user_request = User_Request.objects.get(id = id)
    user_request.delete()
    return JsonResponse({'status' : True, 'message': "Deleted succesfully."})
    
def delete_request(request, id):
    request = Request.objects.get(id=id)
    deleted = request.delete()

    if deleted:
        return JsonResponse({'status': True, 'message': deleted})
    else:
        return JsonResponse({'False': True, 'message': 'Invalid row'})
    
def get_requests(request):
    requests = Request.objects.all()
    requests_json = RequestSerializer(requests, many=True).data  # Serialize the queryset
    return JsonResponse(requests_json, safe=False)

def toggle_request_status(request, id):
    """Toggle the active status of a request form"""
    if request.method == "POST":
        try:
            request_obj = Request.objects.get(id=id)
            
            # Get the new status from POST data or toggle current status
            new_status = request.POST.get('active', None)
            original_status = request_obj.active
            
            if new_status is not None:
                request_obj.active = new_status == 'true' or new_status == True
            else:
                request_obj.active = not request_obj.active
            
            # Log the status change
            print(f"Request {id} status changing from {original_status} to {request_obj.active}")
            
            request_obj.save()
            
            status_text = "active" if request_obj.active else "inactive"
            return JsonResponse({
                'status': True,
                'message': f'Request has been marked as {status_text}',
                'active': request_obj.active,
                'request_id': id
            })
        except Request.DoesNotExist:
            return JsonResponse({
                'status': False,
                'message': 'Request not found'
            }, status=404)
        except Exception as e:
            import traceback
            print(f"Error in toggle_request_status: {str(e)}")
            traceback.print_exc()
            return JsonResponse({
                'status': False,
                'message': f'Error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': False,
        'message': 'Invalid request method'
    }, status=400)

import hashlib
from ..models import generate_key_from_user, encrypt_data, decrypt_data

def handle_uploaded_file(source, file):
    # Define the path where you want to save the file
    static_dir = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(source), 'approved')

    # Create the upload directory if it doesn't exist
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    # Save the file
    file_path = os.path.join(static_dir, file.name)
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    # First hash the path
    hashed_path = hashlib.sha256(file_path.encode()).hexdigest()
    
    # Then encrypt the hashed path
    key = generate_key_from_user(source)
    encrypted_path = encrypt_data(hashed_path, key)
    
    return encrypted_path