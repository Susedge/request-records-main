from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ..models import Document, Requirement, Purpose, Course, ReportTemplate
import os
from django.conf import settings

def index(request):
    selected_table = request.GET.get('table_type', 'Requirement')
    
    if request.method == "POST":
        table_name = request.POST.get("table_name")
        description = request.POST.get("description")
        code = request.POST.get("code")

        try:
            # Check for duplicate code (except for Purpose which doesn't have code)
            if table_name != "Purpose" and code:
                # Determine the model to check against
                model = None
                if table_name == "Requirement":
                    model = Requirement
                elif table_name == "Document":
                    model = Document
                elif table_name == "Course":
                    model = Course
                elif table_name == "Report":
                    model = ReportTemplate
                    # For Report, check name instead of code
                    if model.objects.filter(name=code).exists():
                        return JsonResponse({'status': False, 'message': "Code already exists"})
                
                # For other models, check code field
                if model and model != ReportTemplate and model.objects.filter(code=code).exists():
                    return JsonResponse({'status': False, 'message': "Code already exists"})
            
            # If no duplicate found, proceed with creating the item
            if table_name == "Report":
                template_file = request.FILES.get('template_file')
                if template_file:
                    report = ReportTemplate(
                        name=code or request.POST.get('name'),
                        description=description,
                        template_file=template_file
                    )
                    report.save()
            elif table_name == "Requirement":
                requirement = Requirement(code=code, description=description)
                requirement.save()
            elif table_name == "Document":
                document = Document(code=code, description=description)
                document.save()
            elif table_name == "Purpose":
                purpose = Purpose(description=description, active=True)
                purpose.save()
            elif table_name == "Course":
                course = Course(code=code, description=description)
                course.save()

            return JsonResponse({'status': True, 'message': "Item created successfully"})
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)})        
    else:
        data = None
        
        if selected_table == 'Requirement':
            data = Requirement.objects.all()
        elif selected_table == 'Document':
            data = Document.objects.all()
        elif selected_table == 'Purpose':
            data = Purpose.objects.all()
        elif selected_table == 'Course':
            data = Course.objects.all()
        elif selected_table == 'Report':
            data = ReportTemplate.objects.all()
            
        context = {
            'selected_table': selected_table,
            'data': data
        }
        return render(request, 'code_table/index.html', context)
    
def get_table_data(request):
    table_type = request.GET.get('table_type', 'Requirement')
    
    if table_type == 'Requirement':
        data = list(Requirement.objects.values('id', 'code', 'description'))
    elif table_type == 'Document':
        data = list(Document.objects.values('id', 'code', 'description', 'active'))
    elif table_type == 'Purpose':
        data = list(Purpose.objects.values('id', 'description', 'active'))
    elif table_type == 'Course':
        data = list(Course.objects.values('id', 'code', 'description'))
    elif table_type == 'Report':
        data = list(ReportTemplate.objects.values('id', 'name', 'description', 'template_file'))
        
    return JsonResponse({'data': data})

def check_duplicate(request):
    table_name = request.GET.get('table_name')
    code = request.GET.get('code')
    item_id = request.GET.get('id')
    
    model = None
    if table_name == "Requirement":
        model = Requirement
    elif table_name == "Document":
        model = Document
    elif table_name == "Course":
        model = Course
    elif table_name == "Report":
        model = ReportTemplate
        code = request.GET.get('name', code)
        return JsonResponse({'exists': model.objects.filter(name=code).exclude(id=item_id).exists()})
        
    if model:
        query = model.objects.filter(code=code)
        if item_id:
            query = query.exclude(id=item_id)
        exists = query.exists()
        return JsonResponse({'exists': exists})
    
    return JsonResponse({'exists': False})

@require_POST
def edit(request):
    try:
        table_name = request.POST.get('table_name')
        item_id = request.POST.get('id')
        description = request.POST.get('description')
        code = request.POST.get('code')
        
        if table_name == "Requirement":
            item = get_object_or_404(Requirement, id=item_id)
            item.description = description
            item.code = code
        elif table_name == "Document":
            item = get_object_or_404(Document, id=item_id)
            item.description = description
            item.code = code
        elif table_name == "Purpose":
            item = get_object_or_404(Purpose, id=item_id)
            item.description = description
        elif table_name == "Course":
            item = get_object_or_404(Course, id=item_id)
            item.description = description
            item.code = code
        elif table_name == "Report":
            item = get_object_or_404(ReportTemplate, id=item_id)
            item.description = description
            # For Report, use 'name' instead of 'code'
            item.name = code or request.POST.get('name')
            
        item.save()
        return JsonResponse({'status': True, 'message': 'Item updated successfully'})
    except Exception as e:
        return JsonResponse({'status': False, 'message': str(e)})@require_POST
def delete(request):
    try:
        table_name = request.POST.get('table_name')
        item_id = request.POST.get('id')
        
        if table_name == "Report":
            item = get_object_or_404(ReportTemplate, id=item_id)
            if item.template_file:
                if os.path.exists(item.template_file.path):
                    os.remove(item.template_file.path)
        elif table_name == "Requirement":
            item = get_object_or_404(Requirement, id=item_id)
        elif table_name == "Document":
            item = get_object_or_404(Document, id=item_id)
        elif table_name == "Purpose":
            item = get_object_or_404(Purpose, id=item_id)
        elif table_name == "Course":
            item = get_object_or_404(Course, id=item_id)
            
        item.delete()
        return JsonResponse({'status': True, 'message': 'Item deleted successfully'})
    except Exception as e:
        return JsonResponse({'status': False, 'message': str(e)})
