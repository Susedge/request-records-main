from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from ..models import Course, Record, User, Profile, TempRecord
from django.core import serializers
from ..serializers import RecordSerializer
import json
import os

# Main record view
def index(request):
    courses = Course.objects.all()
    return render(request, 'record/index.html', {'courses': courses})
    
def get_user_data(request):
    # Get all users except admins (user_type=5)
    users = User.objects.exclude(user_type=5)
    
    # Create a list to hold user data with record status
    user_data = []
    
    for user in users:
        # Check if user has a record
        has_record = Record.objects.filter(user_number=user.student_number).exists()
        
        user_dict = {
            'id': user.id,
            'student_number': user.student_number,
            'email': user.email,
            'user_type': user.get_user_type_display(),
            'is_active': user.is_active,
            'has_record': has_record
        }
        
        # Try to get user's name from Record or Profile if available
        try:
            if has_record:
                record = Record.objects.get(user_number=user.student_number)
                user_dict['first_name'] = record.first_name
                user_dict['last_name'] = record.last_name
            elif hasattr(user, 'profile'):
                user_dict['first_name'] = user.profile.first_name
                user_dict['last_name'] = user.profile.last_name
            else:
                user_dict['first_name'] = "Unknown"
                user_dict['last_name'] = "Unknown"
        except:
            user_dict['first_name'] = "Unknown"
            user_dict['last_name'] = "Unknown"
            
        user_data.append(user_dict)
    
    return JsonResponse(json.dumps(user_data), safe=False)
def get_user_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    courses = Course.objects.all()
    
    # Check for existing record
    record_type = "new"
    profile_data = {
        'user_id': user.id,
        'student_number': user.student_number,
        'email': user.email,
        'record_type': 'new'
    }
    
    # Try to find record in Record table
    try:
        record = Record.objects.get(user_number=user.student_number)
        profile_data.update({
            'first_name': record.first_name,
            'middle_name': record.middle_name,
            'last_name': record.last_name,
            'course_code': record.course_code,
            'contact_no': record.contact_no,
            'entry_year_from': record.entry_year_from,
            'entry_year_to': record.entry_year_to,
            'record_type': 'existing'
        })
    except Record.DoesNotExist:
        # Check if user has a temp record from a request
        try:
            # Get the most recent temp record if multiple exist
            temp_record = TempRecord.objects.filter(
                user_request__user=user
            ).order_by('-user_request__created_at').first()
            
            if temp_record:
                profile_data.update({
                    'first_name': temp_record.first_name,
                    'middle_name': temp_record.middle_name,
                    'last_name': temp_record.last_name,
                    'course_code': temp_record.course_code,
                    'contact_no': temp_record.contact_no,
                    'entry_year_from': temp_record.entry_year_from,
                    'entry_year_to': temp_record.entry_year_to,
                    'record_type': 'temp_record'
                })
        except:
            pass
    
    return render(request, 'admin/user/profile_form.html', {
        'profile': profile_data,
        'courses': courses
    })

def save_user_profile(request):
    if request.method == "POST":
        try:
            user_id = request.POST.get('user_id')
            record_type = request.POST.get('record_type')
            user = get_object_or_404(User, id=user_id)
            
            # Prepare data for creating/updating record
            record_data = {
                'user_number': user.student_number,
                'first_name': request.POST.get('first_name'),
                'middle_name': request.POST.get('middle_name'),
                'last_name': request.POST.get('last_name'),
                'course_code': request.POST.get('course_code'),
                'contact_no': request.POST.get('contact_no'),
                'entry_year_from': request.POST.get('entry_year_from'),
                'entry_year_to': request.POST.get('entry_year_to'),
            }
            
            # Create or update record
            record, created = Record.objects.update_or_create(
                user_number=user.student_number,
                defaults=record_data
            )
            
            return JsonResponse({
                'status': True,
                'message': 'Profile updated successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'status': False,
        'message': 'Invalid request method.'
    })

def delete_record(request, id):
    if request.method == "POST":
        try:
            record = Record.objects.get(id=id)
            record_number = record.user_number
            record.delete()
            return JsonResponse({
                'status': True, 
                'message': f'Record {record_number} has been deleted successfully.'
            })
        except Record.DoesNotExist:
            return JsonResponse({
                'status': False, 
                'message': 'Record not found.'
            })
        except Exception as e:
            return JsonResponse({
                'status': False, 
                'message': f'An error occurred: {str(e)}'
            })
    else:
        return JsonResponse({
            'status': False, 
            'message': 'Invalid request method.'
        })


# Add these new functions to the existing record.py file

def get_current_user_profile(request):
    """Get the profile of the currently logged-in user"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': False,
            'message': 'User not authenticated'
        })
    
    courses = Course.objects.all()
    
    # Check for existing record
    record_type = "new"
    profile_data = {
        'user_id': request.user.id,
        'student_number': request.user.student_number,
        'email': request.user.email,
        'record_type': 'new'
    }
    
    # Try to find record in Record table
    try:
        record = Record.objects.get(user_number=request.user.student_number)
        profile_data.update({
            'first_name': record.first_name,
            'middle_name': record.middle_name,
            'last_name': record.last_name,
            'course_code': record.course_code,
            'contact_no': record.contact_no,
            'entry_year_from': record.entry_year_from,
            'entry_year_to': record.entry_year_to,
            'record_type': 'existing'
        })
    except Record.DoesNotExist:
        # Check if user has a temp record from a request
        try:
            # Get the most recent temp record if multiple exist
            temp_record = TempRecord.objects.filter(
                user_request__user=request.user
            ).order_by('-user_request__created_at').first()
            
            if temp_record:
                profile_data.update({
                    'first_name': temp_record.first_name,
                    'middle_name': temp_record.middle_name,
                    'last_name': temp_record.last_name,
                    'course_code': temp_record.course_code,
                    'contact_no': temp_record.contact_no,
                    'entry_year_from': temp_record.entry_year_from,
                    'entry_year_to': temp_record.entry_year_to,
                    'record_type': 'temp_record'
                })
        except:
            pass
    
    # Check if user has a profile with an image
    try:
        user_profile = Profile.objects.get(user=request.user)
        # The profile image will be accessed in the template via the context processor
    except Profile.DoesNotExist:
        pass
    
    return render(request, 'user/profile_form.html', {
        'profile': profile_data,
        'courses': courses
    })

    """Get the profile of the currently logged-in user"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': False,
            'message': 'User not authenticated'
        })
    
    courses = Course.objects.all()
    
    # Check for existing record
    record_type = "new"
    profile_data = {
        'user_id': request.user.id,
        'student_number': request.user.student_number,
        'email': request.user.email,
        'record_type': 'new'
    }
    
    # Try to find record in Record table
    try:
        record = Record.objects.get(user_number=request.user.student_number)
        profile_data.update({
            'first_name': record.first_name,
            'middle_name': record.middle_name,
            'last_name': record.last_name,
            'course_code': record.course_code,
            'contact_no': record.contact_no,
            'entry_year_from': record.entry_year_from,
            'entry_year_to': record.entry_year_to,
            'record_type': 'existing'
        })
    except Record.DoesNotExist:
        # Check if user has a temp record from a request
        try:
            # Get the most recent temp record if multiple exist
            temp_record = TempRecord.objects.filter(
                user_request__user=request.user
            ).order_by('-user_request__created_at').first()
            
            if temp_record:
                profile_data.update({
                    'first_name': temp_record.first_name,
                    'middle_name': temp_record.middle_name,
                    'last_name': temp_record.last_name,
                    'course_code': temp_record.course_code,
                    'contact_no': temp_record.contact_no,
                    'entry_year_from': temp_record.entry_year_from,
                    'entry_year_to': temp_record.entry_year_to,
                    'record_type': 'temp_record'
                })
        except:
            pass
    
    return render(request, 'user/profile_form.html', {
        'profile': profile_data,
        'courses': courses
    })

def save_current_user_profile(request):
    if request.method == "POST":
        try:
            user_id = request.POST.get('user_id')
            record_type = request.POST.get('record_type')
            
            # Ensure the user is only editing their own profile
            if int(user_id) != request.user.id:
                return JsonResponse({
                    'status': False,
                    'message': 'You can only edit your own profile.'
                })
            
            # Prepare data for creating/updating record
            record_data = {
                'user_number': request.user.student_number,
                'first_name': request.POST.get('first_name'),
                'middle_name': request.POST.get('middle_name'),
                'last_name': request.POST.get('last_name'),
                'course_code': request.POST.get('course_code'),
                'contact_no': request.POST.get('contact_no'),
                'entry_year_from': request.POST.get('entry_year_from'),
                'entry_year_to': request.POST.get('entry_year_to'),
            }
            
            # Create or update record
            record, created = Record.objects.update_or_create(
                user_number=request.user.student_number,
                defaults=record_data
            )
            
            # Handle profile image upload
            try:
                # Get or create user profile
                course = Course.objects.get(code=record_data['course_code'])
                profile, created = Profile.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'course': course,
                        'first_name': record_data['first_name'],
                        'middle_name': record_data['middle_name'],
                        'last_name': record_data['last_name'],
                        'contact_no': record_data['contact_no'],
                        'entry_year_from': record_data['entry_year_from'],
                        'entry_year_to': record_data['entry_year_to'],
                    }
                )
                
                # If profile already exists, update its fields
                if not created:
                    profile.course = course
                    profile.first_name = record_data['first_name']
                    profile.middle_name = record_data['middle_name']
                    profile.last_name = record_data['last_name']
                    profile.contact_no = record_data['contact_no']
                    profile.entry_year_from = record_data['entry_year_from']
                    profile.entry_year_to = record_data['entry_year_to']
                
                # Handle profile image if provided
                if 'profile_image' in request.FILES:
                    profile_image = request.FILES['profile_image']
                    # Delete old image if it exists
                    if profile.profile_image:
                        try:
                            if os.path.isfile(profile.profile_image.path):
                                os.remove(profile.profile_image.path)
                        except:
                            pass  # If file doesn't exist or can't be deleted, continue anyway
                    
                    # Save new image
                    profile.profile_image = profile_image
                
                # Save profile
                profile.save()
                
            except Course.DoesNotExist:
                return JsonResponse({
                    'status': False,
                    'message': 'Selected course does not exist.'
                })
            except Exception as e:
                return JsonResponse({
                    'status': False,
                    'message': f'Error updating profile: {str(e)}'
                })
            
            return JsonResponse({
                'status': True,
                'message': 'Profile updated successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'status': False,
        'message': 'Invalid request method.'
    })
