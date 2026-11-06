from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Vehicle


def vehicle_list(request):
    category = request.GET.get('categoria', '')
    vehicles = Vehicle.objects.all()
    if category:
        vehicles = vehicles.filter(category=category)
    return render(request, 'vehicles/list.html', {
        'vehicles': vehicles, 'categories': Vehicle.Category.choices,
        'selected_category': category,
    })


def vehicle_detail(request, pk):
    return render(request, 'vehicles/detail.html', {
        'vehicle': get_object_or_404(Vehicle, pk=pk),
    })

# Create your views here.
