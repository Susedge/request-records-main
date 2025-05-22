from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from docxtpl import DocxTemplate
import os
import time
import shutil
from ..models import ReportTemplate, Purpose, User, Profile, Course, Record
from datetime import datetime
import io
import tempfile
from django.utils.text import slugify
from django.db.models import Q

def admin_reports(request):
    templates = ReportTemplate.objects.all()
    return render(request, 'admin/admin_reports.html', {'templates': templates})

def admin_search_student(request):
    """Search for students by name or student number"""
    query = request.GET.get('query', '').strip()
    
    if not query:
        return JsonResponse([], safe=False)
    
    # Search in User model for student number or email
    user_results = User.objects.filter(
        Q(student_number__icontains=query) | 
        Q(email__icontains=query)
    )
    
    # Search in Profile model for names
    profile_results = Profile.objects.filter(
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query) |
        Q(middle_name__icontains=query)
    ).select_related('user', 'course')
    
    # Search in Record model for names
    record_results = Record.objects.filter(
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query) |
        Q(middle_name__icontains=query) |
        Q(user_number__icontains=query)
    )
    
    # Create a list to hold all user results
    results = []
    processed_user_ids = set()
    processed_user_numbers = set()
    
    # Process users found directly from User search
    for user in user_results:
        if user.id in processed_user_ids:
            continue
            
        processed_user_ids.add(user.id)
        if user.student_number:
            processed_user_numbers.add(user.student_number)
            
        user_data = {
            'id': user.id,
            'student_number': user.student_number or '',
            'email': user.email or '',
            'user_type': user.get_user_type_display() if hasattr(user, 'get_user_type_display') else '',
        }
        
        # First try to get user info from Record model
        try:
            record = Record.objects.get(user_number=user.student_number)
            user_data.update({
                'first_name': record.first_name or '',
                'middle_name': record.middle_name or '',
                'last_name': record.last_name or '',
                'contact_no': record.contact_no or '',
                'entry_year_from': record.entry_year_from or '',
                'entry_year_to': record.entry_year_to or '',
                'course': record.course_code or '',  # Changed to 'course' to match the form field
                'course_code': record.course_code or '',
                'course_description': '', # Record might not have course description
                'suffix': '',  # Add empty suffix field
            })
        except Record.DoesNotExist:
            # If no record, try to get from Profile
            try:
                profile = Profile.objects.get(user=user)
                user_data.update({
                    'first_name': profile.first_name or '',
                    'middle_name': profile.middle_name or '',
                    'last_name': profile.last_name or '',
                    'contact_no': profile.contact_no or '',
                    'entry_year_from': profile.entry_year_from or '',
                    'entry_year_to': profile.entry_year_to or '',
                    'course': profile.course.code if profile.course else '',  # Changed to 'course'
                    'course_code': profile.course.code if profile.course else '',
                    'course_description': profile.course.description if profile.course else '',
                    'suffix': '',  # Add empty suffix field
                })
            except Profile.DoesNotExist:
                # No profile found, set empty values
                user_data.update({
                    'first_name': '',
                    'middle_name': '',
                    'last_name': '',
                    'contact_no': '',
                    'entry_year_from': '',
                    'entry_year_to': '',
                    'course': '',  # Changed to 'course'
                    'course_code': '',
                    'course_description': '',
                    'suffix': '',  # Add empty suffix field
                })
            
        results.append(user_data)
    
    # Process profiles found from Profile search
    for profile in profile_results:
        user = profile.user
        if user.id in processed_user_ids:
            continue
            
        processed_user_ids.add(user.id)
        if user.student_number:
            processed_user_numbers.add(user.student_number)
        
        # First check if user has a record
        try:
            record = Record.objects.get(user_number=user.student_number)
            results.append({
                'id': user.id,
                'student_number': user.student_number or '',
                'email': user.email or '',
                'user_type': user.get_user_type_display() if hasattr(user, 'get_user_type_display') else '',
                'first_name': record.first_name or '',
                'middle_name': record.middle_name or '',
                'last_name': record.last_name or '',
                'contact_no': record.contact_no or '',
                'entry_year_from': record.entry_year_from or '',
                'entry_year_to': record.entry_year_to or '',
                'course': record.course_code or '',  # Changed to 'course'
                'course_code': record.course_code or '',
                'course_description': '', # Record might not have course description
                'suffix': '',  # Add empty suffix field
            })
        except Record.DoesNotExist:
            # If no record exists, use profile data
            results.append({
                'id': user.id,
                'student_number': user.student_number or '',
                'email': user.email or '',
                'user_type': user.get_user_type_display() if hasattr(user, 'get_user_type_display') else '',
                'first_name': profile.first_name or '',
                'middle_name': profile.middle_name or '',
                'last_name': profile.last_name or '',
                'contact_no': profile.contact_no or '',
                'entry_year_from': profile.entry_year_from or '',
                'entry_year_to': profile.entry_year_to or '',
                'course': profile.course.code if profile.course else '',  # Changed to 'course'
                'course_code': profile.course.code if profile.course else '',
                'course_description': profile.course.description if profile.course else '',
                'suffix': '',  # Add empty suffix field
            })
    
    # Process records where we may not have a matching user
    for record in record_results:
        if record.user_number in processed_user_numbers:
            continue  # Skip if we already processed this user
            
        processed_user_numbers.add(record.user_number)
        
        # Try to find the corresponding user
        try:
            user = User.objects.get(student_number=record.user_number)
            if user.id in processed_user_ids:
                continue  # Skip if we already processed this user
                
            processed_user_ids.add(user.id)
            
            results.append({
                'id': user.id,
                'student_number': user.student_number or '',
                'email': user.email or '',
                'user_type': user.get_user_type_display() if hasattr(user, 'get_user_type_display') else '',
                'first_name': record.first_name or '',
                'middle_name': record.middle_name or '',
                'last_name': record.last_name or '',
                'contact_no': record.contact_no or '',
                'entry_year_from': record.entry_year_from or '',
                'entry_year_to': record.entry_year_to or '',
                'course': record.course_code or '',  # Changed to 'course'
                'course_code': record.course_code or '',
                'course_description': '', # Record might not have course description
                'suffix': '',  # Add empty suffix field
            })
        except User.DoesNotExist:
            # This record doesn't have a matching user account
            # We could still include it with a placeholder user ID
            results.append({
                'id': 0,  # Placeholder ID
                'student_number': record.user_number or '',
                'email': '',
                'user_type': 'Unknown',
                'first_name': record.first_name or '',
                'middle_name': record.middle_name or '',
                'last_name': record.last_name or '',
                'contact_no': record.contact_no or '',
                'entry_year_from': record.entry_year_from or '',
                'entry_year_to': record.entry_year_to or '',
                'course': record.course_code or '',  # Changed to 'course'
                'course_code': record.course_code or '',
                'course_description': '', # Record might not have course description
                'suffix': '',  # Add empty suffix field
                'record_only': True  # Flag to indicate this is only from record
            })
    
    return JsonResponse(results, safe=False)

def admin_report_form(request, template_id):
    template = get_object_or_404(ReportTemplate, id=template_id)
    purposes = Purpose.objects.filter(active=True)
    all_courses = Course.objects.all()
    
    # Get student data if provided
    student_data = {}
    student_id = request.GET.get('student_id')
    
    if student_id:
        try:
            user = User.objects.get(id=student_id)
            # Always include user data
            student_data = {
                'student_number': user.student_number or '',
                'email': user.email or '',
                'user_type': user.get_user_type_display() if hasattr(user, 'get_user_type_display') else '',
            }
            
            # First try to get data from Record
            try:
                record = Record.objects.get(user_number=user.student_number)
                student_data.update({
                    'first_name': record.first_name or '',
                    'middle_name': record.middle_name or '',
                    'last_name': record.last_name or '',
                    'suffix': '',  # Add empty suffix as it's not in Record model
                    'contact_no': record.contact_no or '',
                    'entry_year_from': record.entry_year_from or '',
                    'entry_year_to': record.entry_year_to or '',
                    'course': record.course_code or '',
                })
            except Record.DoesNotExist:
                # If no record, try profile
                try:
                    profile = Profile.objects.get(user=user)
                    # Add profile data if available
                    student_data.update({
                        'first_name': profile.first_name or '',
                        'middle_name': profile.middle_name or '',
                        'last_name': profile.last_name or '',
                        'suffix': '',  # Add empty suffix as it might not be in Profile model
                        'contact_no': profile.contact_no or '',
                        'entry_year_from': profile.entry_year_from or '',
                        'entry_year_to': profile.entry_year_to or '',
                        'course': profile.course.code if profile.course else '',
                    })
                except Profile.DoesNotExist:
                    # Set empty profile fields for consistent template rendering
                    student_data.update({
                        'first_name': '',
                        'middle_name': '',
                        'last_name': '',
                        'suffix': '',
                        'contact_no': '',
                        'entry_year_from': '',
                        'entry_year_to': '',
                        'course': '',
                    })
                
        except User.DoesNotExist:
            # If it's a record without a matching user (rare case)
            pass
    
    context = {
        'template': template,
        'purposes': purposes,
        'all_courses': all_courses,
        'student_data': student_data,
    }
    
    return render(request, 'admin/report_form.html', context)

# Add the convert_with_pylovepdf function from admin_reports_old.py
def convert_with_pylovepdf(docx_path, pdf_path):
    """
    Convert DOCX to PDF using the pylovepdf library
    """
    try:
        from pylovepdf.tools.officepdf import OfficeToPdf
        
        # Initialize the task
        task = OfficeToPdf(settings.ILOVEPDF_PUBLIC_KEY, verify_ssl=True, proxies=None)
        
        # Add file to the task
        task.add_file(docx_path)
        
        # Set output folder (same as input folder by default)
        output_dir = os.path.dirname(pdf_path)
        task.set_output_folder(output_dir)
        
        # Process the task
        task.execute()
        
        # Download processed files
        task.download()
        
        # Print debug info about available files
        print(f"Files in output directory after download: {os.listdir(output_dir)}")
        
        # Find the converted PDF file - looking for any PDF file created after task execution
        pdf_found = False
        
        # Get the time before we started processing
        last_modified_time = time.time()
        
        for file in os.listdir(output_dir):
            print(f"Checking file: {file}")
            file_path = os.path.join(output_dir, file)
            
            # Check if this is a PDF file created during this operation
            if file.endswith(".pdf"):
                # Copy the file to the expected location
                try:
                    shutil.copy2(file_path, pdf_path)
                    print(f"Successfully copied to: {pdf_path}")
                    pdf_found = True
                    break
                except Exception as e:
                    print(f"Error copying file: {str(e)}")
        
        # Delete the task from the server
        task.delete_current_task()
        
        # Verify the file exists at the expected location
        if os.path.exists(pdf_path):
            print(f"PDF exists at target path: {pdf_path}")
            with open(pdf_path, 'rb') as f:
                size = len(f.read())
                print(f"PDF file size: {size} bytes")
            return True
        elif pdf_found:
            print(f"PDF was found but may not exist at: {pdf_path}")
            return True
        else:
            print(f"Could not find converted PDF file")
            return False
            
    except Exception as e:
        print(f"PyLovePDF conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def admin_generate_report_pdf(request, template_id):
    if request.method != 'POST':
        return redirect('admin_report_form', template_id=template_id)
    
    template = get_object_or_404(ReportTemplate, id=template_id)
    
    # Get form data
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')
    middle_name = request.POST.get('middle_name', '')
    suffix = request.POST.get('suffix', '')
    output_format = request.POST.get('output_format', 'docx')
    
    # Construct full name with suffix if present
    full_name = f"{first_name} {middle_name} {last_name}"
    if suffix:
        full_name += f", {suffix}"
    
    field_mapping = {
        'first_name': first_name,
        'last_name': last_name,
        'middle_name': middle_name,
        'suffix': suffix,
        'full_name': full_name,
        'contact_no': request.POST.get('contact_no', ''),
        'entry_year_from': request.POST.get('entry_year_from', ''),
        'entry_year_to': request.POST.get('entry_year_to', ''),
        'course': request.POST.get('course', ''),
        'student_number': request.POST.get('student_number', ''),
        'email': request.POST.get('email', ''),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'purpose': request.POST.get('purpose', '')
    }
    
    try:
        # Setup directories
        generated_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'generated')
        os.makedirs(generated_dir, exist_ok=True)
        
        # Ensure proper filename with extension
        safe_name = slugify(template.name)
        if not safe_name:  # In case slugify removes all characters
            safe_name = "report"
        
        docx_path = os.path.join(generated_dir, f"{safe_name}.docx")
        
        # Verify template file exists
        template_path = template.template_file.path
        if not os.path.exists(template_path):
            # Try to find the template relative to MEDIA_ROOT
            alt_path = os.path.join(settings.MEDIA_ROOT, str(template.template_file))
            if os.path.exists(alt_path):
                template_path = alt_path
            else:
                # Last resort - check if we can access it through the URL
                if template.template_file.url and hasattr(template.template_file, 'file'):
                    template_path = template.template_file.file.name
                else:
                    raise FileNotFoundError(f"Template file not found at {template_path}")
        
        # Process document using docxtpl for better template handling
        print(f"Using template file from: {template_path}")
        doc_template = DocxTemplate(template_path)
        doc_template.render(field_mapping)
        doc_template.save(docx_path)
        
        # Handle PDF conversion if needed
        if output_format == 'pdf':
            pdf_path = os.path.join(generated_dir, f"{safe_name}.pdf")
            
            # Use PyLovePDF for conversion instead of docx2pdf
            print(f"Starting PDF conversion with PyLovePDF...")
            if not convert_with_pylovepdf(docx_path, pdf_path):
                raise Exception("PyLovePDF conversion failed. Check logs for details.")
            
            print(f"PDF conversion completed successfully.")
            
            # Serve the PDF
            output_filename = f"{safe_name}.pdf"
            response = FileResponse(
                open(pdf_path, 'rb'),
                content_type='application/pdf'
            )
            
            # Set Content-Disposition header
            response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
            
            # Clean up both files after streaming
            response._resource_closers.append(lambda: os.remove(docx_path))
            response._resource_closers.append(lambda: os.remove(pdf_path))
            
        else:
            # Serve the DOCX with explicit content disposition header
            output_filename = f"{safe_name}.docx"
            response = FileResponse(
                open(docx_path, 'rb'),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            # Set explicit Content-Disposition header
            response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
            
            # Add file cleanup after streaming
            response._resource_closers.append(lambda: os.remove(docx_path))
        
        return response
                
    except Exception as e:
        import traceback
        error_msg = f"Error generating document: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise Http404(error_msg)
