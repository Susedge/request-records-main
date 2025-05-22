from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from docxtpl import DocxTemplate
import os
from ..models import ReportTemplate, Purpose, User, Profile, Course
from datetime import datetime
import io
import tempfile
from django.utils.text import slugify
import pythoncom
from docx2pdf import convert  # You'll need to pip install docx2pdf
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
    
    # Combine the results
    results = []
    
    # Add results from user search
    for user in user_results:
        try:
            # Try to get the associated profile
            profile = Profile.objects.get(user=user)
            results.append({
                'id': user.id,
                'student_number': user.student_number,
                'email': user.email,
                'first_name': profile.first_name,
                'middle_name': profile.middle_name,
                'last_name': profile.last_name,
                'contact_no': profile.contact_no,
                'entry_year_from': profile.entry_year_from,
                'entry_year_to': profile.entry_year_to,
                'course_code': profile.course.code if profile.course else '',
                'course_description': profile.course.description if profile.course else '',
            })
        except Profile.DoesNotExist:
            # User without profile
            results.append({
                'id': user.id,
                'student_number': user.student_number,
                'email': user.email,
                'first_name': '',
                'middle_name': '',
                'last_name': '',
                'contact_no': '',
                'entry_year_from': '',
                'entry_year_to': '',
                'course_code': '',
                'course_description': '',
            })
    
    # Add results from profile search (if not already added)
    for profile in profile_results:
        user_id = profile.user.id
        # Check if this user is already in results
        if not any(r['id'] == user_id for r in results):
            results.append({
                'id': user_id,
                'student_number': profile.user.student_number,
                'email': profile.user.email,
                'first_name': profile.first_name,
                'middle_name': profile.middle_name,
                'last_name': profile.last_name,
                'contact_no': profile.contact_no,
                'entry_year_from': profile.entry_year_from,
                'entry_year_to': profile.entry_year_to,
                'course_code': profile.course.code if profile.course else '',
                'course_description': profile.course.description if profile.course else '',
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
            try:
                profile = Profile.objects.get(user=user)
                student_data = {
                    'student_number': user.student_number,
                    'email': user.email,
                    'first_name': profile.first_name,
                    'middle_name': profile.middle_name,
                    'last_name': profile.last_name,
                    'contact_no': profile.contact_no,
                    'entry_year_from': profile.entry_year_from,
                    'entry_year_to': profile.entry_year_to,
                    'course': profile.course.code if profile.course else '',
                }
            except Profile.DoesNotExist:
                # Just include user data without profile
                student_data = {
                    'student_number': user.student_number,
                    'email': user.email,
                }
        except User.DoesNotExist:
            pass
    
    context = {
        'template': template,
        'purposes': purposes,
        'all_courses': all_courses,
        'student_data': student_data,
    }
    
    return render(request, 'admin/report_form.html', context)

def admin_generate_report_pdf(request, template_id):
    if request.method != 'POST':
        return redirect('admin_report_form', template_id=template_id)
    
    template = get_object_or_404(ReportTemplate, id=template_id)
    
    # Get form data
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')
    middle_name = request.POST.get('middle_name', '')
    suffix = request.POST.get('suffix', '')  # Get the suffix value
    output_format = request.POST.get('output_format', 'docx')  # Get selected format
    
    # Construct full name with suffix if present
    full_name = f"{first_name} {middle_name} {last_name}"
    if suffix:
        full_name += f", {suffix}"
    
    field_mapping = {
        'first_name': first_name,
        'last_name': last_name,
        'middle_name': middle_name,
        'suffix': suffix,  # Add suffix to the template variables
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
        
        # Process document using docxtpl for better template handling
        doc_template = DocxTemplate(template.template_file.path)
        doc_template.render(field_mapping)
        doc_template.save(docx_path)
        
        # Handle PDF conversion if needed
        if output_format == 'pdf':
            pdf_path = os.path.join(generated_dir, f"{safe_name}.pdf")
            # Initialize COM for PDF conversion
            pythoncom.CoInitialize()
            # Convert DOCX to PDF
            convert(docx_path, pdf_path)
            
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
        raise Http404(f"Error generating document: {str(e)}")
