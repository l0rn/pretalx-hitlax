import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

# Mock some pretalx and django stuff if needed
from unittest.mock import MagicMock

# Import necessary modules so that pretalx_hitalx can import them
import django
from django.conf import settings
if not settings.configured:
    settings.configure()

try:
    from pretalx_hitalx import views
    print("Views imported successfully")
except Exception as e:
    print(f"Error importing views: {e}")
    import traceback
    traceback.print_exc()

try:
    from pretalx_hitalx import signals
    print("Signals imported successfully")
except Exception as e:
    print(f"Error importing signals: {e}")
    import traceback
    traceback.print_exc()
