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
        
        # Initialize the task - Add the required proxies parameter
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
        
        # Find the downloaded file (it will be named differently)
        for file in os.listdir(output_dir):
            if file.endswith(".pdf") and file.startswith(os.path.splitext(os.path.basename(docx_path))[0]):
                downloaded_pdf = os.path.join(output_dir, file)
                if downloaded_pdf != pdf_path and os.path.exists(downloaded_pdf):
                    shutil.move(downloaded_pdf, pdf_path)
                    break
        
        # Delete the task from the server
        task.delete_current_task()
        
        return os.path.exists(pdf_path)
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
            
            # Try different PDF conversion methods
            conversion_successful = False
            error_messages = []
            
            # Method 1: Try PyLovePDF (official ILovePDF library)
            try:
                if convert_with_pylovepdf(docx_path, pdf_path):
                    conversion_successful = True
                else:
                    error_messages.append("PyLovePDF conversion failed")
            except Exception as e:
                error_messages.append(f"PyLovePDF error: {str(e)}")
            
            # Method 2: Try docx2pdf if PyLovePDF failed
            if not conversion_successful:
                try:
                    from docx2pdf import convert
                    convert(docx_path, pdf_path)
                    conversion_successful = True
                except Exception as e:
                    error_messages.append(f"docx2pdf error: {str(e)}")
            
            # Method 3: Try LibreOffice if available and previous methods failed
            if not conversion_successful:
                try:
                    subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', 
                                   '--outdir', generated_dir, docx_path], check=True)
                    
                    # LibreOffice creates PDF with the same base name
                    libreoffice_pdf = os.path.join(generated_dir, os.path.splitext(os.path.basename(docx_path))[0] + '.pdf')
                    if os.path.exists(libreoffice_pdf) and libreoffice_pdf != pdf_path:
                        shutil.move(libreoffice_pdf, pdf_path)
                        
                    conversion_successful = True
                except Exception as e:
                    error_messages.append(f"LibreOffice error: {str(e)}")
            
            # Method A: Last resort - crude text extraction (no images or proper formatting)
            if not conversion_successful:
                try:
                    # Create a basic PDF with just text content
                    doc_content = docx2python(docx_path)
                    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
                    styles = getSampleStyleSheet()
                    flowables = []
                    
                    for table in doc_content.body:
                        for row in table:
                            for cell in row:
                                for paragraph in cell:
                                    if paragraph:
                                        p = Paragraph(paragraph, styles['Normal'])
                                        flowables.append(p)
                                        flowables.append(Spacer(1, 0.2 * inch))
                    
                    # Build the PDF document
                    doc.build(flowables)
                    conversion_successful = True
                except Exception as e:
                    error_messages.append(f"Fallback PDF creation error: {str(e)}")
            
            # If all conversion methods failed, raise an error
            if not conversion_successful:
                raise Exception(f"All PDF conversion methods failed: {'; '.join(error_messages)}")
            
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