from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import os
import hashlib
from django.conf import settings
from ..models import User_Request, Requirement, generate_key_from_user, encrypt_data

def check_request_status(request, request_id):
    """Check if a request is approved and ready for requirement uploads"""
    try:
        user_request = User_Request.objects.get(id=request_id, user=request.user)
        return JsonResponse({
            'status': user_request.status,
            'approved': user_request.approved,  
            'can_upload': user_request.approved and user_request.status != "Completed"
        })
    except User_Request.DoesNotExist:
        return JsonResponse({
            'status': 'not_found',
            'message': 'Request not found'
        }, status=404)

def get_requirements(request, request_id):
    """Get the requirements for a specific user request"""
    try:
        user_request = User_Request.objects.get(id=request_id, user=request.user)
        
        # Only return requirements if request is approved
        if not user_request.approved:
            return JsonResponse({
                'status': False,
                'message': 'This request is pending approval. Requirements will be available after approval.'
            })
        
        # Get requirements from the associated Request model
        requirement_codes = user_request.request.files_required_as_list()
        requirements = []
        
        for code in requirement_codes:
            try:
                requirement = Requirement.objects.get(code=code)
                requirements.append({
                    'code': code,
                    'description': requirement.description
                })
            except Requirement.DoesNotExist:
                requirements.append({
                    'code': code,
                    'description': f"Document: {code}"
                })
        
        return JsonResponse({
            'status': True,
            'requirements': requirements
        })
    except User_Request.DoesNotExist:
        return JsonResponse({
            'status': False,
            'message': 'Request not found'
        }, status=404)

def upload_requirements(request, request_id):
    """Handle uploading requirements for an approved request"""
    if request.method != 'POST':
        return JsonResponse({'status': False, 'message': 'Invalid request method'})
    
    try:
        user_request = User_Request.objects.get(id=request_id, user=request.user)
        
        # Enhanced debugging
        print(f"Request method: {request.method}")
        print(f"Request FILES keys: {list(request.FILES.keys())}")
        print(f"Request POST keys: {list(request.POST.keys())}")
        
        # Verify request is approved (uncomment for production)
        if not user_request.approved:
            return JsonResponse({
                'status': False,
                'message': 'This request is pending approval and cannot accept uploads yet.'
            })
        
        # Check if any files were uploaded with better error message
        if not request.FILES:
            return JsonResponse({
                'status': False,
                'message': 'No files were detected in the request. Please ensure you have selected files to upload.'
            })
            
        uploads = []
        
        # Process each uploaded file 
        for file_code, file_obj in request.FILES.items():
            # Skip any non-file fields
            if not hasattr(file_obj, 'name'):
                continue
                
            print(f"Processing file '{file_code}': {file_obj.name} ({file_obj.size} bytes)")
            
            try:
                # Save the file
                file_path = save_uploaded_file(file_obj, user_request.id, file_code)
                
                # Create the hash and encrypted path
                file_hash = hashlib.sha256(file_path.encode()).hexdigest()
                key = generate_key_from_user(str(user_request.id))
                encrypted_path = encrypt_data(file_hash, key)
                
                # Add to uploads with file code identifier
                file_prefix = "<" + file_code + "&>"
                uploads.append(file_prefix + encrypted_path)
                
                print(f"Successfully processed file: {file_code}")
                
            except Exception as e:
                print(f"Error processing file {file_code}: {str(e)}")
                import traceback
                print(traceback.format_exc())
                return JsonResponse({
                    'status': False,
                    'message': f'Error processing file {file_code}: {str(e)}'
                })
        
        # Update the user request with new uploads
        if uploads:
            # Combine with existing uploads if any
            existing_uploads = user_request.uploads or ""
            if existing_uploads and existing_uploads.strip():
                existing_uploads += ","
                
            user_request.uploads = existing_uploads + ",".join(uploads)
            
            # Update status to indicate requirements have been uploaded
            if user_request.status == "Processing":
                user_request.status = "Requirements Submitted"
                
            user_request.save()
            
            return JsonResponse({
                'status': True,
                'message': 'Requirements uploaded successfully! Your request is now being processed.'
            })
        else:
            return JsonResponse({
                'status': False,
                'message': 'Files could not be processed. Please try again.'
            })
            
    except User_Request.DoesNotExist:
        return JsonResponse({
            'status': False,
            'message': 'Request not found'
        }, status=404)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in upload_requirements: {error_traceback}")
        return JsonResponse({
            'status': False,
            'message': f'Error: {str(e)}'
        }, status=500)

def save_uploaded_file(file_obj, user_request_id, file_code):
    """Helper function to save an uploaded file"""
    static_dir = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(user_request_id))
    
    # Create the upload directory if it doesn't exist
    os.makedirs(static_dir, exist_ok=True)
    
    # Create a more organized filename with the file code
    filename = f"{file_code}_{file_obj.name}"
    
    # Save the file
    file_path = os.path.join(static_dir, filename)
    with open(file_path, 'wb+') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)
            
    return file_path

def handle_uploaded_file(request_id, requirement_code, file):
    """Save uploaded file and return encrypted path"""
    # Create directory if it doesn't exist
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'user', 'user_request', str(request_id))
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Save file with requirement code as prefix to avoid overwrites
    filename = f"{requirement_code}_{file.name}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    # Hash and encrypt the path
    hashed_path = hashlib.sha256(file_path.encode()).hexdigest()
    key = generate_key_from_user(request_id)
    encrypted_path = encrypt_data(hashed_path, key)
    
    return encrypted_path