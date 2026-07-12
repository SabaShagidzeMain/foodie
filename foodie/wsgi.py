import os
import sys
from django.core.wsgi import get_wsgi_application

# Add your project path to sys.path
path = '/home/yourusername/foodie'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodie.settings')

application = get_wsgi_application()