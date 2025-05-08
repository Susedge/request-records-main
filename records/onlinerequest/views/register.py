import os
import json
import random
import string
import smtplib
from email.mime.text import MIMEText
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from ..forms import UserRegistrationForm
from ..models import RegisterRequest
from ..models import Course
from ..models import Record
from ..models import User
from ..models import Profile

ENABLE_OTP_VERIFICATION = False

def generate_verification_code(length=6):
    characters = string.ascii_letters + string.digits
    verification_code = ''.join(random.choice(characters) for _ in range(length))
    return verification_code

@require_POST
def send_verification_email(request):
    email = request.POST.get('email')
    if email:
        verification_code = generate_verification_code()
        request.session['verification_code'] = verification_code
        request.session['user_email'] = email
        expiry_time = 5  # 5 minutes
        request.session.set_expiry(expiry_time * 60)

        send_email_with_code(email, verification_code, expiry_time, message_type='otp')

        return JsonResponse({'status': True, 'message': 'Verification code sent to your email'})
    else:
        return JsonResponse({'status': False, 'message': 'Email is required'})

def send_email_with_code(email, verification_code, expiry_time, message_type='otp'):
    """
    Send an email with a code/password depending on the message_type.
    
    Parameters:
    - email: recipient email address
    - verification_code: the code or password to send
    - expiry_time: time in minutes until expiry (0 for no expiry)
    - message_type: 'otp', 'approval', or 'reset'
    """
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = settings.EMAIL_HOST_USER
    smtp_password = settings.EMAIL_HOST_PASSWORD

    # Format the expiry time display for OTP messages
    expiry_display = ""
    if expiry_time > 0:
        if expiry_time < 60:  # Less than an hour
            expiry_display = f"{expiry_time} minutes"
        elif expiry_time < 1440:  # Less than a day (24 hours = 1440 minutes)
            hours = expiry_time // 60
            expiry_display = f"{hours} hours"
        else:  # More than a day
            from datetime import datetime, timedelta
            expiry_date = datetime.now() + timedelta(minutes=expiry_time)
            expiry_display = expiry_date.strftime("%B %d, %Y at %I:%M %p")
    
    # Set subject based on message type
    if message_type == 'otp':
        subject = 'Email Verification Code'
    elif message_type == 'approval':
        subject = 'Account Approved'
    elif message_type == 'reset':
        subject = 'Password Reset'
    else:
        subject = 'TAU-ARS'
    
    # Build message based on type
    if message_type == 'otp':
        message = f"""
        <html>
        <body>
            <p>This code will expire in <strong style="font-size: 1.2em; color: #c00;">{expiry_display}</strong> or when you leave the registration page.</p>
            <p style="font-size: 1.1em; color: #333;">Your verification code is:</p>
            <h1 style="text-align: center; font-size: 3em; color: #007bff; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);"> {verification_code} </h1>
        </body>
        </html>
        """
    elif message_type == 'approval':
        message = f"""
        <html>
        <body>
            <h2>Account Approved!</h2>
            <p>Your account has been approved. Here are your login credentials:</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Password:</strong> {verification_code}</p>
            <p>Please login with this password.</p>
        </body>
        </html>
        """
    elif message_type == 'reset':
        message = f"""
        <html>
        <body>
            <h2>Password Reset</h2>
            <p>Your password has been reset by an administrator. Here are your new login credentials:</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Password:</strong> {verification_code}</p>
            <p>Please login with this new password.</p>
        </body>
        </html>
        """

    msg = MIMEText(message, 'html')
    msg['Subject'] = subject
    msg['From'] = 'TAU-ARS<{}>'.format(smtp_username)
    msg['To'] = email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, email, msg.as_string())

from django.shortcuts import render, redirect

def index(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Set is_active to True - no need for approval
            user.is_active = True
            
            # Set user_type to unspecified (0)
            user.user_type = 0  # Unspecified
            
            # Skip verification code check if OTP is disabled
            if ENABLE_OTP_VERIFICATION:
                entered_code = form.cleaned_data.get('verification_code')
                stored_code = request.session.get('verification_code')

                if entered_code != stored_code:
                    return JsonResponse({'status': False, 'message': 'Invalid verification code'})
            
            # Get the raw password before it's hashed
            raw_password = form.cleaned_data.get('password')
            
            # Student number will be auto-generated in the save method if not provided
            
            # Save the user
            user.save()
            
            # Store user email and password in session for reference in unauthenticated requests
            request.session['temp_user_email'] = user.email
            request.session['temp_user_password'] = raw_password
            
            # Return success message and redirect to /request/
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # If AJAX request, return JSON
                return JsonResponse({
                    'status': True, 
                    'message': 'Registration successful! You can now create a request.',
                    'redirect': '/request/'  # Redirect URL to /request/
                })
            else:
                # For non-AJAX requests, redirect directly
                return redirect('/request/')        
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                last_error_message = list(form.errors.items())[0]
                return JsonResponse({'status': False, 'message': last_error_message[1]})
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})
    
def handle_uploaded_file(file):
    # Define the path where you want to save the file
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')

    # Create the upload directory if it doesn't exist
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Save the file
    file_path = os.path.join(upload_dir, file.name)
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return file_path
