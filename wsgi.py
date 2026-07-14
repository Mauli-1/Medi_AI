"""WSGI entry point for production servers (gunicorn, uWSGI, etc.)

Usage with gunicorn:
    gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application

Usage with uWSGI:
    uwsgi --http 0.0.0.0:8000 --module wsgi:application --processes 4
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

application = create_app(os.environ.get('FLASK_ENV', 'production'))

# Gunicorn also accepts the name 'app'
app = application
