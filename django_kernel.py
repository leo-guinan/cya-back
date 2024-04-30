import os
import sys
from IPython.core.interactiveshell import InteractiveShell

# Path to the directory of your Django project
sys.path.append("/Users/leoguinan/PycharmProjects/cya-back")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Allows full interaction with the Django project in Jupyter
import django
django.setup()

# Optional: use auto-reload to see changes in Django code automatically
InteractiveShell.instance().extension_manager.load_extension('autoreload')
InteractiveShell.instance().extension_manager.enable_extension('autoreload')
InteractiveShell.instance().extension_manager.configure('autoreload', {'autoreload': 2})