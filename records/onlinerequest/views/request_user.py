from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.response import Response
from django.conf import settings
from ..models import Request, User_Request, Requirement, User
from ..serializers import RequestSerializer
from ..utilities import get_if_exists
import json
from django.core import serializers
import os

def index(request):
      all_requests = Request.objects.filter(active=True)
      return render(request, 'user/request/index.html', {'all_requests': all_requests})

from django.contrib.auth import login, authenticate

def create_request(request):
    if request.method == 'POST':
        try:
            user = request.user if request.user.is_authenticated else None
            
            # Get request data
            post_request_id = request.POST.get('request')
            post_purpose = request.POST.get('purpose')
            post_purpose_other = request.POST.get('purpose_other')
            post_number_of_copies = request.POST.get('number_of_copies', 1)
            
            # Debug logging
            print(f"Creating request: ID={post_request_id}, Purpose={post_purpose}, Copies={post_number_of_copies}")
            
            # Validate request is active
            try:
                request_obj = Request.objects.get(id=post_request_id)
                # Double-check that the request is active
                if not request_obj.active:
                    print(f"Request {post_request_id} is not active")
                    return JsonResponse({
                        'status': False,
                        'message': 'The selected request type is no longer available. Please choose another.'
                    })
            except Request.DoesNotExist:
                print(f"Request {post_request_id} not found")
                return JsonResponse({
                    'status': False,
                    'message': 'The selected request type does not exist. Please choose another.'
                })
            
            # Set purpose based on selection
            if post_purpose == 'Others' and post_purpose_other:
                final_purpose = post_purpose_other
            else:
                final_purpose = post_purpose

            # Create a new user request
            uploads = ""

            # Check if user is authenticated
            if request.user.is_authenticated:
                # Use the authenticated user
                user = request.user
            else:
                # For anonymous users, try to find user by email from session
                user_email = request.session.get('temp_user_email')
                user_password = request.session.get('temp_user_password')
            
                if not user_email:
                    return JsonResponse({'status': False, 'message': 'Profile information is required for unauthenticated users. Please register first.'})
            
                try:
                    # First try to get the user
                    user = User.objects.get(email=user_email)
                    
                    # Then authenticate with stored credentials
                    if user_password:
                        authenticated_user = authenticate(request, username=user_email, password=user_password)
                        if authenticated_user:
                            login(request, authenticated_user)
                            user = authenticated_user
                            print(f"User authenticated: {request.user.is_authenticated}")
                        else:
                            # Fallback to the old method if authentication fails
                            user.backend = 'django.contrib.auth.backends.ModelBackend'
                            login(request, user)
                            print(f"User authenticated (fallback): {request.user.is_authenticated}")
                    else:
                        # Fallback if no password in session
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        login(request, user)
                        print(f"User authenticated (no password): {request.user.is_authenticated}")
                
                except User.DoesNotExist:
                    return JsonResponse({'status': False, 'message': 'User not found. Please register or login first.'})
        
            # Create user request
            user_request = User_Request(
                user=user,
                request=request_obj,
                status="Processing",  # Changed from "Payment not yet settled" to "Processing"
                purpose=final_purpose,
                number_of_copies=int(post_number_of_copies),
                payment_status="Approved"  # Set a default payment status
            )
        
            # Update user type immediately if provided
            if 'user_type' in request.POST and user:
                user.user_type = int(request.POST.get('user_type'))
                user.save()
        
            # Store temp_user_info if available
            if 'temp_user_info' in request.POST:
                temp_user_info = json.loads(request.POST.get('temp_user_info'))
                user_request.temp_user_info = temp_user_info

            # Pre-save the object to get an ID
            user_request.save()

            # Create TempRecord if temp_user_info is available
            if hasattr(user_request, 'temp_user_info') and user_request.temp_user_info:
                from ..models import TempRecord
            
                # Create TempRecord entry
                temp_record = TempRecord(
                    user_request=user_request,
                    user_number=user.student_number,
                    first_name=temp_user_info.get('first_name', ''),
                    last_name=temp_user_info.get('last_name', ''),
                    middle_name=temp_user_info.get('middle_name', ''),
                    contact_no=temp_user_info.get('contact_no', ''),
                    course_code=temp_user_info.get('course', ''),
                    entry_year_from=int(temp_user_info.get('entry_year_from', 0)),
                    entry_year_to=int(temp_user_info.get('entry_year_to', 0))
                )
                temp_record.save()

            # Upload and encrypt required files
            for file_name in request.FILES:
                file = request.FILES.get(file_name)
                
                # Handle authorization letter separately
                if file_name == 'authorization_letter':
                    encrypted_path = handle_uploaded_file(file, str(user_request.id), 'authorization_letter')
                    user_request.authorization_letter = encrypted_path
                else:
                    encrypted_path = handle_uploaded_file(file, str(user_request.id))
                    file_prefix = "<" + file_name + "&>"
                    uploads += file_prefix + encrypted_path + ","

            user_request.uploads = uploads.rstrip(',')
            user_request.save()
        
            print(f"Successfully created request ID={user_request.id}")
            return JsonResponse({
                'status': True, 
                'message': 'Successfully created request! Your request is now being processed.',
                'id': user_request.id,
                'redirect': '/request/user/'  # Redirect to user requests page instead of payment
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error creating request: {str(e)}")
            return JsonResponse({
                'status': False,
                'message': f'An error occurred: {str(e)}'
            })
            
    return JsonResponse({'status': False, 'message': 'Invalid request method'})

def get_request(request, id): 
    try:
        # Add debug logging
        print(f"Looking up request with ID: {id}")
        
        # Explicitly check if the request exists first
        try:
            request_obj = Request.objects.get(id=id)
        except Request.DoesNotExist:
            print(f"Request with ID {id} not found")
            return JsonResponse({
                "error": "Request not found. Please refresh and try again.",
                "active": False,
                "code": "not_found"
            }, status=404)
        
        # Now check if it's active
        print(f"Request found, active status: {request_obj.active}")
        if not request_obj.active:
            return JsonResponse({
                "error": "The selected request type is no longer available. Please choose another.",
                "active": False,
                "code": "inactive"
            }, status=404)
        
        # If active, proceed as normal
        request_serializer = RequestSerializer(request_obj)
        return JsonResponse(request_serializer.data, safe=False)
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error in get_request: {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            "error": f"An unexpected error occurred: {str(e)}",
            "active": False,
            "code": "error"
        }, status=500)

def get_active_requests(request):
    """Get only active requests for real-time updates"""
    try:
        active_requests = Request.objects.filter(active=True)
        
        # If there are no active requests, return an empty list but with a 200 status
        if not active_requests.exists():
            return JsonResponse([], safe=False)
            
        active_requests_json = RequestSerializer(active_requests, many=True).data
        return JsonResponse(active_requests_json, safe=False)
    except Exception as e:
        # Log the error
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "error": f"Failed to retrieve active requests: {str(e)}"
        }, status=500)

import hashlib
from ..models import generate_key_from_user, encrypt_data, decrypt_data

def handle_uploaded_file(file, source, file_type=""):
    try:
        # Define the path where you want to save the file
        if file_type == 'authorization_letter':
            static_dir = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(source), 'authorization_letter')
        else:
            static_dir = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(source))

        # Create the upload directory if it doesn't exist
        os.makedirs(static_dir, exist_ok=True)

        # Save the file
        file_path = os.path.join(static_dir, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Hash the file path
        hashed_path = hashlib.sha256(file_path.encode()).hexdigest()
        
        # Encrypt the hashed path
        key = generate_key_from_user(source)
        encrypted_path = encrypt_data(hashed_path, key)
        
        return encrypted_path
    except Exception as e:
        raise Exception(f"Error handling file upload: {str(e)}")

def get_document_description(request, doc_code):
    try:
        document = Requirement.objects.get(code=doc_code)
        return JsonResponse({'description': document.description})
    except Requirement.DoesNotExist:
        return JsonResponse({'description': 'Document not found'}, status=404)

from django.contrib.auth import login

# This function is modified to simply redirect to the user dashboard
def display_payment(request, id):
    # Just redirect to the user requests page
    return redirect('/request/user/')

def display_user_requests(request):
    try:
        # Check if user is authenticated before querying
        if not request.user.is_authenticated:
            # Redirect to login page or show a message
            return render(request, 'user/request/view-user-request.html', {
                'user_requests': [],
                'message': 'Please log in to view your requests'
            })
        
        # Now we know we have an authenticated user with a valid ID
        # Include only user requests with active request types
        user_requests = User_Request.objects.filter(
            user=request.user,
            request__active=True
        )
        
        for user_request in user_requests:
            # Decrypt requested file path if exists
            if user_request.requested:
                key = generate_key_from_user(str(user_request.id))
                decrypted_hash = decrypt_data(user_request.requested, key)
                base_path = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(user_request.id), 'approved')
                
                if os.path.exists(base_path):
                    for filename in os.listdir(base_path):
                        file_path = os.path.join(base_path, filename)
                        current_hash = hashlib.sha256(file_path.encode()).hexdigest()
                        if current_hash == decrypted_hash:
                            user_request.requested = file_path
                            break

            # Decrypt authorization letter if exists
            if hasattr(user_request, 'authorization_letter') and user_request.authorization_letter:
                key = generate_key_from_user(str(user_request.id))
                decrypted_hash = decrypt_data(user_request.authorization_letter, key)
                base_path = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(user_request.id), 'authorization_letter')
                
                if os.path.exists(base_path):
                    for filename in os.listdir(base_path):
                        file_path = os.path.join(base_path, filename)
                        current_hash = hashlib.sha256(file_path.encode()).hexdigest()
                        if current_hash == decrypted_hash:
                            user_request.authorization_letter_path = file_path
                            user_request.has_authorization_letter = True
                            break
                    else:
                        user_request.has_authorization_letter = False
                else:
                    user_request.has_authorization_letter = False
            else:
                user_request.has_authorization_letter = False

            # Set a default payment status if needed
            if not user_request.payment_status:
                user_request.payment_status = "Approved"
                user_request.save()

        return render(request, 'user/request/view-user-request.html', {'user_requests': user_requests})
    except Exception as e:
        # Add more detailed error information
        import traceback
        error_details = traceback.format_exc()
        print(error_details)  # Log the full traceback
        return HttpResponse(f"Error displaying user requests: {str(e)}")

import qrcode
from io import BytesIO
import base64

def generate_qr(request, id):
    try:
        user_request = User_Request.objects.get(id=id)
        if request.user != user_request.user:
            return HttpResponse("Unauthorized access", status=403)
            
        verification_url = request.build_absolute_uri(f'/verify-document/{id}/')
        document_name = user_request.request.document.description
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image = base64.b64encode(buffer.getvalue()).decode()
        
        return render(request, 'user/request/qr-code.html', {
            'qr_code': qr_image,
            'document_name': document_name
        })
    except User_Request.DoesNotExist:
        return HttpResponse("Request not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error generating QR code: {str(e)}")

def verify_document(request, document_id):
    try:
        user_request = User_Request.objects.get(id=document_id)
        
        context = {
            'document_name': user_request.request.document.description,
            'verification_date': user_request.updated_at,
            'student_number': user_request.user.student_number,
            'system_name': 'Academic Request System (ARS)'
        }
        
        return render(request, 'user/request/verify-document.html', context)
    except User_Request.DoesNotExist:
        return HttpResponse("Invalid document verification code", status=404)

# Add a new function to download authorization letter
def download_authorization_letter(request, id):
    try:
        user_request = User_Request.objects.get(id=id)
        
        # Check if user is authorized to download
        if request.user.is_authenticated and (request.user == user_request.user or request.user.user_type == 5):  # User or admin
            # Decrypt the authorization letter path
            if not user_request.authorization_letter:
                return HttpResponse("No authorization letter found for this request", status=404)
                
            key = generate_key_from_user(str(user_request.id))
            decrypted_hash = decrypt_data(user_request.authorization_letter, key)
            base_path = os.path.join(settings.MEDIA_ROOT, 'onlinerequest', 'static', 'user_request', str(user_request.id), 'authorization_letter')
            
            if os.path.exists(base_path):
                for filename in os.listdir(base_path):
                    file_path = os.path.join(base_path, filename)
                    current_hash = hashlib.sha256(file_path.encode()).hexdigest()
                    if current_hash == decrypted_hash:
                        # Serve the file
                        if os.path.exists(file_path):
                            with open(file_path, 'rb') as fh:
                                response = HttpResponse(fh.read(), content_type='application/octet-stream')
                                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                                return response
                        else:
                            return HttpResponse("File not found", status=404)
                
                return HttpResponse("Authorization letter not found", status=404)
            else:
                return HttpResponse("Authorization letter directory not found", status=404)
        else:
            return HttpResponse("Unauthorized access", status=403)
    except User_Request.DoesNotExist:
        return HttpResponse("Request not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error downloading authorization letter: {str(e)}", status=500)

def get_requirements(request, request_id):
    """Get the requirements for a specific user request"""
    try:
        user_request = User_Request.objects.get(id=request_id, user=request.user)
        
        # Only return requirements if status is Approved
        if user_request.status != "Approved":
            return JsonResponse({
                'status': False,
                'message': 'Requirements are only available for approved requests.'
            })
        
        # Get requirements from approved_requirements field
        requirement_codes = user_request.get_approved_requirements()
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
