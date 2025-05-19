from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.conf import settings
from docxtpl import DocxTemplate
import os
from ..models import Profile, ReportTemplate, Purpose, Course
from datetime import datetime
import io
import tempfile
import time
import shutil
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    templates = ReportTemplate.objects.all()
    purposes = Purpose.objects.filter(active=True)
    all_courses = Course.objects.all()
    
    return render(request, 'user/reports.html', {
        'templates': templates, 
        'purposes': purposes,
        'all_courses': all_courses,
    })

@login_required
def report_form(request, template_id):
    template = get_object_or_404(ReportTemplate, id=template_id)
    purposes = Purpose.objects.filter(active=True)
    all_courses = Course.objects.all()
    
    # Get user profile for auto-filling
    try:
        profile = Profile.objects.get(user=request.user)
        user_data = {
            'first_name': profile.first_name,
            'last_name': profile.last_name,
            'middle_name': profile.middle_name,
            'contact_no': profile.contact_no,
            'entry_year_from': profile.entry_year_from,
            'entry_year_to': profile.entry_year_to,
            'course': profile.course.code if profile.course else '',
            'student_number': request.user.student_number,
            'email': request.user.email,
        }
    except Profile.DoesNotExist:
        user_data = {
            'first_name': '',
            'last_name': '', 
            'middle_name': '',
            'contact_no': '',
            'entry_year_from': '',
            'entry_year_to': '',
            'course': '',
            'student_number': request.user.student_number if hasattr(request.user, 'student_number') else '',
            'email': request.user.email if hasattr(request.user, 'email') else '',
        }
    
    return render(request, 'user/report_form.html', {
        'template': template,
        'purposes': purposes,
        'all_courses': all_courses,
        'user_data': user_data
    })

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

@login_required
def generate_report_pdf(request, template_id):
    if request.method != 'POST':
        return redirect('report_form', template_id=template_id)
    
    template = get_object_or_404(ReportTemplate, id=template_id)
    
    # Get form data
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')
    middle_name = request.POST.get('middle_name', '')
    suffix = request.POST.get('suffix', '')
    output_format = request.POST.get('output_format', 'pdf')  # Default to PDF
    display_mode = request.POST.get('display_mode', 'inline')  # Default to inline viewing
    
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
        
        # Create unique filename to prevent collisions
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        safe_name = slugify(f"{template.name}_{request.user.id}_{timestamp}")
        if not safe_name:
            safe_name = f"report_{timestamp}"
        
        docx_path = os.path.join(generated_dir, f"{safe_name}.docx")
        
        # Process document using docxtpl for better template handling
        doc_template = DocxTemplate(template.template_file.path)
        doc_template.render(field_mapping)
        doc_template.save(docx_path)
        
        # Handle PDF conversion if needed
        if output_format == 'pdf':
            pdf_path = os.path.join(generated_dir, f"{safe_name}.pdf")
            
            # Convert using PyLovePDF instead of docx2pdf
            print(f"Starting PDF conversion with PyLovePDF...")
            if not convert_with_pylovepdf(docx_path, pdf_path):
                raise Exception("PyLovePDF conversion failed. Check logs for details.")
            
            print(f"PDF conversion completed successfully.")
            print(f"Output PDF path: {pdf_path}")
            print(f"PDF exists: {os.path.exists(pdf_path)}")
            
            # After conversion
            if not os.path.exists(pdf_path):
                print(f"Critical: PDF not found at {pdf_path} after conversion")
                print(f"Generated dir contents: {os.listdir(generated_dir)}")
            else:
                try:
                    # Check file is readable
                    with open(pdf_path, 'rb') as f:
                        first_bytes = f.read(100)
                        print(f"PDF file can be opened and read ({len(first_bytes)} bytes read)")
                except Exception as open_error:
                    print(f"Error opening PDF file: {str(open_error)}")
            
            # Determine appropriate filename for the user
            output_filename = f"{template.name.replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.pdf"
            
            # Serve the PDF with appropriate disposition
            response = FileResponse(
                open(pdf_path, 'rb'),
                content_type='application/pdf'
            )
            
            # Set disposition based on user preference
            if display_mode == 'download':
                response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
            else:
                response['Content-Disposition'] = f'inline; filename="{output_filename}"'
            
            # Clean up both files after streaming
            response._resource_closers.append(lambda: os.remove(docx_path))
            response._resource_closers.append(lambda: os.remove(pdf_path))
            
        else:
            # Serve the DOCX for download
            output_filename = f"{template.name.replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.docx"
            response = FileResponse(
                open(docx_path, 'rb'),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            # DOCX files are always downloaded
            response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
            
            # Add file cleanup after streaming
            response._resource_closers.append(lambda: os.remove(docx_path))
        
        return response
                
    except Exception as e:
        raise Http404(f"Error generating document: {str(e)}")
