from django.shortcuts import render
from django.conf import settings
from django.http import FileResponse
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_GET
from urllib.parse import urlsplit
from vehicles.models import Vehicle


def home(request):
    return render(request, 'core/home.html', {'featured_vehicles': Vehicle.objects.order_by('pk')[:3],
        'hero_vehicle': Vehicle.objects.filter(brand='Toyota', model='Corolla').first(),
        'categories': Vehicle.Category.choices})

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


@require_GET
def offline_catalog(request):
    """Copia pública sin request, usuario, CSRF ni datos de rentas o del asistente."""
    from vehicles.photos import get_reference_photos

    items = []
    for vehicle in Vehicle.objects.all():
        image = vehicle.image.url if vehicle.image else ''
        parts = urlsplit(image)
        if (parts.scheme or parts.netloc or parts.query or parts.fragment
                or not parts.path.startswith('/media/vehicles/')):
            image = f'/static/images/{vehicle.category}.svg'
        items.append({'vehicle': vehicle, 'image': image})
    generated = timezone.now().isoformat()
    html = render_to_string('vehicles/offline_catalog.html', {
        'items': items, 'generated': generated,
        'images': sorted({item['image'] for item in items}), 'photos': get_reference_photos(),
    })
    response = HttpResponse(html)
    response['Cache-Control'] = 'no-cache'
    response['X-DriveSmart-Public-Catalog'] = '1'
    response['X-DriveSmart-Catalog-Date'] = generated
    return response
