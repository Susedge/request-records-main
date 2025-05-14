from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.conf import settings
from docxtpl import DocxTemplate
import os
import subprocess
import shutil
import requests
import json
from ..models import ReportTemplate, Purpose
from datetime import datetime
import io
import tempfile
from django.utils.text import slugify
from docx2python import docx2python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def admin_reports(request):
    templates = ReportTemplate.objects.all()
    return render(request, 'admin/admin_reports.html', {'templates': templates})

def admin_report_form(request, template_id):
    template = get_object_or_404(ReportTemplate, id=template_id)
    purposes = Purpose.objects.filter(active=True)
    return render(request, 'admin/report_form.html', {
        'template': template,
        'purposes': purposes
    })

def convert_with_pylovepdf(docx_path, pdf_path):
    """
    Convert DOCX to PDF using the pylovepdf library
    """
    try:
        from pylovepdf.tools.officepdf import OfficeToPdf
        
        # Initialize the task with required proxies parameter
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
        
        # The PyLovePDF library typically appends '_officepdf_<date>' to the filename
        # Find the converted file
        converted_found = False
        base_name = os.path.splitext(os.path.basename(docx_path))[0]
        for file in os.listdir(output_dir):
            print(f"Checking file: {file}")
            if file.endswith(".pdf") and file.startswith(base_name):
                downloaded_pdf = os.path.join(output_dir, file)
                print(f"Found converted file: {downloaded_pdf}")
                
                # Move or copy the file to the expected path
                try:
                    shutil.copy2(downloaded_pdf, pdf_path)
                    print(f"Successfully copied to: {pdf_path}")
                    converted_found = True
                    break
                except Exception as e:
                    print(f"Error copying file: {str(e)}")
                    # Try to move the file instead
                    try:
                        shutil.move(downloaded_pdf, pdf_path)
                        print(f"Successfully moved to: {pdf_path}")
                        converted_found = True
                        break
                    except Exception as move_error:
                        print(f"Error moving file: {str(move_error)}")
        
        # Delete the task from the server
        task.delete_current_task()
        
        # Verify the file exists at the expected location
        if os.path.exists(pdf_path):
            print(f"PDF exists at target path: {pdf_path}")
            return True
        elif converted_found:
            print(f"File was found but may not exist at final path: {pdf_path}")
            return True
        else:
            print(f"Could not find converted PDF file")
            return False
            
    except Exception as e:
        print(f"PyLovePDF conversion error: {str(e)}")
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
        if not safe_name:
            safe_name = "report"
        
        docx_path = os.path.join(generated_dir, f"{safe_name}.docx")
        
        # Fix the template file path
        template_path = template.template_file.path
        
        # Check if the path is missing "records/" and fix it
        if '/reports/templates/' in template_path and not os.path.exists(template_path):
            corrected_path = template_path.replace('/reports/templates/', '/records/reports/templates/')
            if os.path.exists(corrected_path):
                template_path = corrected_path
        
        # Use the corrected path
        doc_template = DocxTemplate(template_path)
        doc_template.render(field_mapping)
        doc_template.save(docx_path)
        
        # Handle PDF conversion if needed
        if output_format == 'pdf':
            pdf_path = os.path.join(generated_dir, f"{safe_name}.pdf")
            
            # Only use PyLovePDF for conversion
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
            
            # Serve the PDF
            output_filename = f"{safe_name}.pdf"
            response = FileResponse(
                open(pdf_path, 'rb'),
                content_type='application/pdf'
            )
            
            # Set Content-Disposition header
            response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
            
            # Clean up files after streaming
            response._resource_closers.append(lambda: os.remove(docx_path))
            response._resource_closers.append(lambda: os.remove(pdf_path))
            
        else:
            # Serve the DOCX file
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