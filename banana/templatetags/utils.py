from django import template
from django.core.files.storage import default_storage
from django.contrib.staticfiles import finders

register = template.Library()

@register.filter(name='file_exists')
def file_exists(filepath):
    result = finders.find(filepath)
    if default_storage.exists(result):
        return True
    else:
        return False