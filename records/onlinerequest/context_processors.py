from onlinerequest.models import Record, Request, Profile, Course, Document

def user_record(request):
    if request.user.is_authenticated:
        try:
            user_record = Record.objects.get(user_number=request.user.student_number)
            return {'user_record': user_record}
        except Record.DoesNotExist:
            return {'user_record': None}
    return {'user_record': None}

def request_forms(request):
    request_forms = Request.objects.all()
    return {'request_forms': request_forms}

def user_profile(request):
    """Make the user's profile available to all templates if authenticated"""
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            return {'user_profile': profile}
        except Profile.DoesNotExist:
            return {'user_profile': None}
    return {'user_profile': None}

def user_requests(request):
    """Make the user's requests available to all templates if authenticated"""
    if request.user.is_authenticated:
        from onlinerequest.models import User_Request
        user_requests = User_Request.objects.filter(
            user=request.user,
            request__active=True
        )
        return {'user_requests_global': user_requests}
    return {'user_requests_global': []}

def courses(request):
    """Make all courses available to templates"""
    all_courses = Course.objects.all()
    return {'all_courses': all_courses}

def document_types(request):
    """Make all document types available to templates"""
    all_document_types = Document.objects.all().order_by('description')
    return {'all_document_types': all_document_types}