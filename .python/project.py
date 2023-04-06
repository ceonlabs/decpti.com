import os
from django.conf import settings
from django.core import management
from django.conf.urls import url
from django.http import HttpResponse

# Django 2.2 Release Notes
# https://docs.djangoproject.com/en/4.1/releases/2.2/
# Documentation
# https://docs.djangoproject.com/en/2.2/

__version__ = 0.1

DEBUG = True
ROOT_URLCONF = 'project'
DATABASES = {'default': { 'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'project.db' }}
SECRET_KEY = os.getenv('SECRET_KEY', 'Please set a SECRET_KEY as an env var.')

if not settings.configured:
    settings.configure(**locals())

def index(request):
    return HttpResponse('Hello Django!')

urlpatterns = [
    url(r'^$', index),
]

if __name__ == '__main__':  # pragma: no cover
    management.execute_from_command_line()