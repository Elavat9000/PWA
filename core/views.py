from django.shortcuts import render
from django.conf import settings
from django.http import FileResponse


def home(request):
    return render(request, 'core/home.html')

# Create your views here.


def _pwa_file(filename, content_type):
    response = FileResponse((settings.BASE_DIR / 'static' / 'pwa' / filename).open('rb'),
                            content_type=content_type)
    response['Cache-Control'] = 'no-cache'
    return response


def manifest(request):
    return _pwa_file('manifest.webmanifest', 'application/manifest+json')


def service_worker(request):
    response = _pwa_file('service-worker.js', 'application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


def offline(request):
    return _pwa_file('offline.html', 'text/html; charset=utf-8')
