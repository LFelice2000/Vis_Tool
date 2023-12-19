"""
ASGI config for web_scrapper project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import get_default_application

import sys

sys.path.append('/Vis_Tool')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_scrapper.settings')

application = get_default_application()
