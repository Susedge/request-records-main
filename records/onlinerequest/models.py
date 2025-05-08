from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
from django.utils import timezone
import os

def generate_key_from_user(user_id):
    return hashlib.sha256(str(user_id).encode()).digest()

def encrypt_data(data, key):
    if not data:
        return ''
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    data_bytes = data.encode()
    ciphertext, tag = cipher.encrypt_and_digest(data_bytes)
    return base64.b64encode(nonce + tag + ciphertext).decode('utf-8')

def decrypt_data(encrypted_data, key):
    if not encrypted_data:
        return ''
    try:
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        nonce = encrypted_bytes[:16]
        tag = encrypted_bytes[16:32]
        ciphertext = encrypted_bytes[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag)
        return data.decode('utf-8')
    except:
        return ''

class Record(models.Model):
    user_number = models.CharField(max_length=10)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    course_code = models.CharField(max_length=5)
    middle_name = models.CharField(max_length=64, default='De Guz Man')
    contact_no = models.IntegerField(default='09667614313')
    entry_year_from = models.IntegerField()
    entry_year_to = models.IntegerField()

    def __str__(self):
        return self.user_number
    
class Course(models.Model):
    code = models.CharField(max_length=64)
    description = models.CharField(max_length=64)

class Requirement(models.Model):
    code = models.CharField(max_length=64)
    description = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.code} - {self.description}"
    
class Code(models.Model):
    table_name = models.CharField(max_length=64)

class User(AbstractBaseUser):
      USER_TYPE_CHOICES = (
        (0, 'unspecified'),
        (1, 'student'),
        (2, 'faculty'),  # Changed from 'teacher' to 'faculty'
        (3, 'alumni'),
        (5, 'admin'),
        (6, 'guest'),
        (7, 'authorized person'),  # Added new option
      )

      student_number = models.CharField(max_length=64, unique=True, blank=True, null=True)
      email = models.EmailField(max_length=254, unique=True)
      password = models.CharField(max_length=256)
      is_active = models.BooleanField(default=False)
      # Add these required admin fields
      is_staff = models.BooleanField(default=False)  # Required for admin access
      is_superuser = models.BooleanField(default=False)  # Required for full admin permissions
      user_type = models.PositiveSmallIntegerField(choices = USER_TYPE_CHOICES, default = 0)  # Default to unspecified

      USERNAME_FIELD = 'email'
      REQUIRED_FIELDS = []

      # Add these permission methods that are required for admin
      def has_perm(self, perm, obj=None):
          return self.is_superuser

      def has_module_perms(self, app_label):
          return self.is_superuser

      def __str__(self):
          return self.student_number or self.email

      def get_user_type_display(self):
          return dict(self.USER_TYPE_CHOICES).get(self.user_type, 'Unknown')
      
      def save(self, *args, **kwargs):
          # Generate student number if not provided
          if not self.student_number:
              super().save(*args, **kwargs)
              self.student_number = f"ID-{self.id:06d}"  # Format: ID-000001, ID-000002, etc.
              return super().save(update_fields=['student_number'])
          else:
              super().save(*args, **kwargs)  

# Function to handle profile image upload paths
def profile_image_path(instance, filename):
    # Get the file extension
    ext = filename.split('.')[-1]
    # Generate a new filename using the user's ID
    new_filename = f"profile_{instance.user.id}.{ext}"
    # Return the upload path
    return os.path.join('profile_images', new_filename)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    middle_name = models.CharField(max_length=64, default='De Guz Man')
    contact_no = models.IntegerField(default='09667614313')
    entry_year_from = models.IntegerField(default='2018')
    entry_year_to = models.IntegerField(default='2024')
    profile_image = models.ImageField(upload_to=profile_image_path, blank=True, null=True)

    def __str__(self):
        return self.first_name
    
    def get_profile_image_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        else:
            # Return a default image URL using static
            from django.templatetags.static import static
            return static('assets/img/default-profile.jpg')

class RegisterRequest(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = "register_request")
    valid_id = models.CharField(max_length=254)

class Document(models.Model):
    code = models.CharField(max_length=64)
    description = models.CharField(max_length=64)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.description

class Request(models.Model):
    description = models.CharField(max_length=256)
    files_required = models.CharField(max_length=256)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    price = models.CharField(max_length=6, default=1.00)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.document.description
    
    def delete(self, *args, **kwargs):
        deleted_title = self.description
        super().delete(*args, **kwargs)
        return f"Request '{deleted_title}' has been deleted"
    
    def files_required_as_list(self):
        return self.files_required.split(',')

class User_Request(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_requests')
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='user_requests')
    status = models.CharField(max_length=64)
    uploads = models.TextField()  
    requested = models.CharField(max_length=256, default="")
    purpose = models.CharField(max_length=256, blank=True)
    number_of_copies = models.IntegerField(default=1)
    uploaded_payment = models.TextField(blank=True)
    payment_status = models.CharField(max_length=10, default="Processing", blank=True)
    authorization_letter = models.TextField(blank=True)
    schedule = models.DateTimeField(null=True, blank=True)  # Pickup schedule
    date_release = models.DateTimeField(null=True, blank=True)  # Date of release/pickup
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_requirements = models.TextField(blank=True, null=True)
    approved = models.BooleanField(default=False)

    def set_uploads(self, uploads_list):
        if not uploads_list:
            self.uploads = ''
            return
        
        key = generate_key_from_user(self.user.id)
        encrypted_paths = [encrypt_data(path, key) for path in uploads_list]
        self.uploads = ','.join(encrypted_paths)

    def get_uploads(self):
        if not self.uploads:
            return []
        
        key = generate_key_from_user(self.user.id)
        encrypted_paths = self.uploads.split(',')
        return [decrypt_data(path, key) for path in encrypted_paths]

    def uploads_as_list(self):
        return self.get_uploads()
    
    def calculate_date_release(self):
        """Calculate expected release date based on processing time"""
        if self.schedule:
            return self.schedule
        
        # Default: 3 business days from creation date if no schedule is set
        processing_days = 3
        
        if hasattr(self, 'processing_time'):
            try:
                processing_days = int(self.processing_time)
            except (ValueError, AttributeError):
                pass
                
        release_date = self.created_at + timezone.timedelta(days=processing_days)
        return release_date

    def set_authorization_letter(self, file_path):
        if not file_path:
            self.authorization_letter = ''
            return
        
        key = generate_key_from_user(self.user.id)
        self.authorization_letter = encrypt_data(file_path, key)

    def get_authorization_letter(self):
        if not self.authorization_letter:
            return None
        
        key = generate_key_from_user(self.user.id)
        return decrypt_data(self.authorization_letter, key)

    def set_approved_requirements(self, requirements_list):
        if not requirements_list:
            self.approved_requirements = ''
            return
        
        key = generate_key_from_user(self.user.id)
        encrypted_requirements = [encrypt_data(req, key) for req in requirements_list]
        self.approved_requirements = ','.join(encrypted_requirements)
    
    def get_approved_requirements(self):
        if not self.approved_requirements:
            return []
        
        key = generate_key_from_user(self.user.id)
        if not self.approved_requirements:
            return []
        encrypted_requirements = self.approved_requirements.split(',')
        return [decrypt_data(req, key) for req in encrypted_requirements]

class Purpose(models.Model):
    description = models.CharField(max_length=256)
    active = models.BooleanField(default=True)

class ReportTemplate(models.Model):
    name = models.CharField(max_length=255)
    template_file = models.FileField(upload_to='reports/templates/')
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TempRecord(models.Model):
    user_request = models.OneToOneField(User_Request, on_delete=models.CASCADE, related_name='temp_record')
    user_number = models.CharField(max_length=10, blank=True, null=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    course_code = models.CharField(max_length=5)
    middle_name = models.CharField(max_length=64, blank=True, null=True)
    contact_no = models.CharField(max_length=20)  # Changed to CharField to handle various formats
    entry_year_from = models.IntegerField()
    entry_year_to = models.IntegerField()
    
    def __str__(self):
        return f"Temp Record for {self.first_name} {self.last_name}"

class DatabaseBackup(models.Model):
    backup_file = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=True)
    file_size = models.IntegerField(default=0)  # Size in bytes
    
    def __str__(self):
        return f"Backup on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_file_size_display(self):
        """Convert file size to human-readable format"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.2f} {unit}"
            size /= 1024
