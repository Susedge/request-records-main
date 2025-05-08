from django.shortcuts import render
from django.http import JsonResponse
from ..models import User, Record, TempRecord, Course
from django.core import serializers
import json

def user_list(request):
    users = User.objects.all()
    
    # Prepare user data with record status
    user_data = []
    for user in users:
        has_record = Record.objects.filter(user_number=user.student_number).exists()
        
        user_data.append({
            'id': user.id,
            'student_number': user.student_number,
            'email': user.email,
            'user_type': user.get_user_type_display(),
            'is_active': user.is_active,
            'has_record': has_record
        })
    
    courses = Course.objects.all()
    return render(request, 'admin/user/index.html', {'users': user_data, 'courses': courses})

def get_user_profile(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        record = Record.objects.filter(user_number=user.student_number).first()
        
        if record:
            profile_data = {
                'user_id': user.id,
                'student_number': user.student_number,
                'email': user.email,
                'first_name': record.first_name,
                'middle_name': record.middle_name,
                'last_name': record.last_name,
                'course_code': record.course_code,
                'contact_no': record.contact_no,
                'entry_year_from': record.entry_year_from,
                'entry_year_to': record.entry_year_to,
                'record_type': 'existing'
            }
        else:
            # Check for temp record
            temp_requests = user.user_requests.all()
            temp_record = None
            
            for user_request in temp_requests:
                try:
                    temp_record = user_request.temp_record
                    if temp_record:
                        break
                except TempRecord.DoesNotExist:
                    continue
            
            if temp_record:
                profile_data = {
                    'user_id': user.id,
                    'student_number': user.student_number,
                    'email': user.email,
                    'first_name': temp_record.first_name,
                    'middle_name': temp_record.middle_name,
                    'last_name': temp_record.last_name,
                    'course_code': temp_record.course_code,
                    'contact_no': temp_record.contact_no,
                    'entry_year_from': temp_record.entry_year_from,
                    'entry_year_to': temp_record.entry_year_to,
                    'record_type': 'temp_record'
                }
            else:
                profile_data = {
                    'user_id': user.id,
                    'student_number': user.student_number,
                    'email': user.email,
                    'first_name': '',
                    'middle_name': '',
                    'last_name': '',
                    'course_code': '',
                    'contact_no': '',
                    'entry_year_from': 2024,
                    'entry_year_to': 2024,
                    'record_type': 'new'
                }
        
        courses = Course.objects.all()
        return render(request, 'admin/user/profile_form.html', {'profile': profile_data, 'courses': courses})
    
    except User.DoesNotExist:
        return JsonResponse({'status': False, 'message': 'User not found'})

def save_user_profile(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        record_type = request.POST.get('record_type')
        
        try:
            user = User.objects.get(id=user_id)
            
            # Prepare record data
            record_data = {
                'user_number': user.student_number,
                'first_name': request.POST.get('first_name'),
                'middle_name': request.POST.get('middle_name'),
                'last_name': request.POST.get('last_name'),
                'course_code': request.POST.get('course_code'),
                'contact_no': request.POST.get('contact_no'),
                'entry_year_from': request.POST.get('entry_year_from'),
                'entry_year_to': request.POST.get('entry_year_to')
            }
            
            # Create or update record
            record, created = Record.objects.update_or_create(
                user_number=user.student_number,
                defaults=record_data
            )
            
            # If this was a temp record, we've now created a permanent one
            if record_type == 'temp_record':
                # We don't delete the temp record as it might be needed for reference
                pass
                
            return JsonResponse({
                'status': True, 
                'message': 'User profile saved successfully'
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'status': False, 
                'message': 'User not found'
            })
        except Exception as e:
            return JsonResponse({
                'status': False, 
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'status': False, 
        'message': 'Invalid request method'
    })
