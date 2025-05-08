from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
from ..models import User
from .register import generate_verification_code, send_email_with_code
from django.core import management
import threading

def index(request):
    if request.method == "POST":
        if 'verify_otp' in request.POST:
            # OTP verification logic remains the same
            entered_otp = request.POST.get('otp')
            stored_otp = request.session.get('login_otp')
            email = request.session.get('temp_login_email')
            
            if entered_otp == stored_otp:
                user = authenticate(request, username=email, password=request.session.get('temp_login_password'))
                if user is not None:
                    login(request, user)
                    return JsonResponse({'status': True, 'message': 'Logged in successfully'})
            return JsonResponse({'status': False, 'message': 'Invalid OTP'})
            
        else:
            email = request.POST.get("email")
            password = request.POST.get("password")
            
            user = authenticate(request, username=email, password=password)

            if user is not None:
                if not user.is_active:
                    return JsonResponse({'status': False, 'message': 'Account not yet activated. Please contact your administrator.'})
                
                # Skip OTP for admin users (user_type = 5)
                if user.user_type == 5:
                    login(request, user)
                    
                    # Trigger database backup when admin logs in (in a background thread)
                    def run_backup_thread():
                        management.call_command('run_scheduled_backups', verbosity=0)
                    
                    backup_thread = threading.Thread(target=run_backup_thread)
                    backup_thread.daemon = True
                    backup_thread.start()
                    
                    return JsonResponse({'status': True, 'message': 'Logged in as administrator'})
                
                # Generate and send OTP for non-admin users
                otp = generate_verification_code()
                request.session['login_otp'] = otp
                request.session['temp_login_email'] = email
                request.session['temp_login_password'] = password
                request.session.set_expiry(300)
                
                send_email_with_code(email, otp, 5)
                return JsonResponse({'status': True, 'message': 'Please verify OTP sent to your email', 'require_otp': True})
            else:
                return JsonResponse({'status': False, 'message': 'Invalid email and password'})
    else:
        return render(request, 'login.html')
