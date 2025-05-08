from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
import os
import shutil

@login_required
def upload_qr_code(request):
    # Create a dedicated QR codes directory
    qr_codes_dir = os.path.join(settings.STATICFILES_DIRS[0], 'assets', 'qr_codes')
    os.makedirs(qr_codes_dir, exist_ok=True)
    
    # Path for the specific payment method QR code
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        qr_image = request.FILES.get('qr_image')
        
        if not payment_method:
            messages.error(request, "Payment method is required")
            return redirect('upload_qr_code')
            
        # Normalize payment method name for filename (lowercase, no spaces)
        filename = f"{payment_method.lower().replace(' ', '_')}.jpg"
        static_qr_path = os.path.join(qr_codes_dir, filename)
        
        if qr_image:
            # Validate file size
            if qr_image.size > 5 * 1024 * 1024:  # 5MB limit
                messages.error(request, "File size exceeds 5MB limit")
                return redirect('upload_qr_code')
                
            # Validate file type
            if not qr_image.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                messages.error(request, "Only JPG and PNG files are allowed")
                return redirect('upload_qr_code')
            
            file_exists = os.path.exists(static_qr_path)
            
            # Make backup of existing QR code if it exists
            if file_exists:
                backup_path = static_qr_path + '.backup'
                shutil.copy2(static_qr_path, backup_path)
                action_msg = "updated"
            else:
                action_msg = "created"
            
            # Save the new QR code
            with open(static_qr_path, 'wb+') as destination:
                for chunk in qr_image.chunks():
                    destination.write(chunk)
            
            messages.success(request, f"QR code for {payment_method} {action_msg} successfully")
            return redirect('upload_qr_code')
    
    # For GET request - list all available payment QR codes
    payment_method = request.GET.get('payment_method', 'GCASH')
    filename = f"{payment_method.lower().replace(' ', '_')}.jpg"
    static_qr_path = os.path.join(qr_codes_dir, filename)
    
    current_qr = None
    if os.path.exists(static_qr_path):
        current_qr = f"{settings.STATIC_URL}assets/qr_codes/{filename}"
    
    # Get list of available payment methods from existing QR codes
    payment_methods = []
    if os.path.exists(qr_codes_dir):
        for file in os.listdir(qr_codes_dir):
            if file.endswith(('.jpg', '.jpeg', '.png')):
                method_name = os.path.splitext(file)[0].replace('_', ' ').upper()
                payment_methods.append(method_name)
    
    return render(request, 'admin/qr_upload.html', {
        'current_qr': current_qr,
        'current_method': payment_method,
        'payment_methods': payment_methods
    })
