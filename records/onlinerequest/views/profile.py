import json
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.forms.models import model_to_dict
from ..models import Profile, User
from ..forms import ProfileForm
from ..utilities import *

def index(request):
    # Get authneticated user
    user = request.user
    user_profile = get_if_exists(Profile, user = user)

    if request.method == "GET":
        if user_profile:
            return render(request, 'user/profile.html', { 'profile': user_profile })
        
        return HttpResponse("Profile not yet created. Please consult your administrator")
    
    elif request.method == "POST":
        if user_profile:
            #  Data
            data = json.loads(request.body)

            # Edit profile fields
            user_profile.contact_no = data.get('contact_no')

            # Convert profile to dict
            data = model_to_dict(user_profile)

            # Get form instance
            profile_form = ProfileForm(data, instance = user_profile)
            
            if profile_form.is_valid():
                profile_form.save()
                return JsonResponse({'message': "Profile saved."})
            else:
                return JsonResponse({'errors': profile_form.errors}, status = 400)
        
    return JsonResponse({'error': 'Only POST and GET requests are allowed'}, status = 405)
