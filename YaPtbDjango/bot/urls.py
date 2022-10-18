from django.conf import settings
from django.urls import re_path

from . import views

webhook_base = settings.TELEGRAMBOT.get('WEBHOOK_PREFIX', '/')
if webhook_base.startswith("/"):
    webhook_base = webhook_base[1:]
if not webhook_base.endswith("/"):
    webhook_base += "/"

# https://uniwebsidad.com/libros/django-1-0/capitulo-3/mapeando-urls-a-vistas
urlpatterns = [
    re_path(r'bot/$', views.home, name='bot'),
    re_path(r'^$', views.webhook, name='webhook'),
]
