import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the project directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'records'))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'records.settings')
application = get_wsgi_application()
