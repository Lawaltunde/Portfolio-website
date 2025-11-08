import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from com.hammed.app import create_app

# WSGI application entrypoint
app = create_app()