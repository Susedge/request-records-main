from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login as auth_login
from django.urls import reverse
from ..models import Record, User
import random
import string
import logging

logger = logging.getLogger(__name__)

def index(request):
    if request.method == "POST":
        print(request.POST)
        if request.POST:
            command_name = request.POST.get("command-name")  # Will serve as command key

            if command_name == "REQUEST":
                reference_number = request.POST.get("reference-number")
                user_record = Record.objects.filter(user_number=reference_number).first()

                if user_record:
                    # Get user reference with user_type guest
                    user = User.objects.filter(student_number=reference_number, user_type=6).first()
                    if user:
                        auth_login(request, user)
                        # If user is logged in redirect user to dashboard
                        return JsonResponse({'status': True, 'redirect_url': reverse('request_user')})
                    else:
                        return JsonResponse({'status': False, 'message': 'Invalid reference number'})
                else:
                    return JsonResponse({'status': False, 'message': 'User does not exist'})

        return JsonResponse({'status': False, 'message': 'Posted Successfully'})
    else:
        return render(request, 'reference-login.html')

def generate_reference_number():
    return ''.join(random.choices(string.digits, k=10))

def create_request(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        middle_name = request.POST.get("middle_name", "")  # Default to empty string if not provided
        email = request.POST.get("email")
        contact_no = request.POST.get("contact_no")
        entry_year_from = request.POST.get("entry_year_from")
        entry_year_to = request.POST.get("entry_year_to")

        reference_number = generate_reference_number()

        # Create a new Record
        record = Record.objects.create(
            user_number=reference_number,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            contact_no=contact_no,
            entry_year_from=entry_year_from,
            entry_year_to=entry_year_to
        )

        # Create a new User with user_type set to guest
        user = User.objects.create(
            student_number=reference_number,
            email=email,
            is_active=True,
            user_type=6  # Set user_type to guest
        )

        # Log the user in
        auth_login(request, user)

        logger.info(f'Created user with user_type: {user.user_type}')

        return JsonResponse({'status': True, 'message': 'Request created successfully', 'reference_number': reference_number})
    else:
        return HttpResponse("Invalid request method", status=405)
