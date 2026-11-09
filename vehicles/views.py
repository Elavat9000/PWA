from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Vehicle
from .forms import CatalogFilterForm
from .photos import get_reference_photos


def vehicle_list(request):
    form = CatalogFilterForm(request.GET)
    vehicles = Vehicle.objects.all()
    if form.is_valid():
        data = form.cleaned_data
        for parameter, lookup in [('categoria', 'category'), ('marca', 'brand'),
                ('transmision', 'transmission'), ('pasajeros', 'passengers__gte'),
                ('precio_max', 'daily_price__lte')]:
            if data[parameter] not in (None, ''):
                vehicles = vehicles.filter(**{lookup: data[parameter]})
        if data['disponibles']:
            vehicles = vehicles.filter(available=True)
        ordering = {'precio_asc': 'daily_price', 'precio_desc': '-daily_price'}
        if data['orden'] in ordering:
            vehicles = vehicles.order_by(ordering[data['orden']], 'pk')
    else:
        vehicles = vehicles.none()
    return render(request, 'vehicles/list.html', {'vehicles': vehicles, 'filter_form': form})


def image_credits(request):
    return render(request, 'vehicles/credits.html', {'photos': get_reference_photos()})


def vehicle_detail(request, pk):
    return render(request, 'vehicles/detail.html', {
        'vehicle': get_object_or_404(Vehicle, pk=pk),
    })

# Create your views here.
