from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from vehicles.models import Vehicle
from .forms import RentalRequestForm
from .models import RentalRequest


@login_required
@require_http_methods(['GET', 'POST'])
def rental_create(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    rental = RentalRequest(user=request.user, vehicle=vehicle)
    form = RentalRequestForm(request.POST if request.method == 'POST' else None, instance=rental)
    quote = None
    if request.method == 'POST' and form.is_valid():
        quote = {'days': rental.days, 'total': vehicle.daily_price * rental.days}
        if request.POST.get('action') == 'confirm':
            try:
                rental.save()
            except ValidationError as error:
                form.add_error(None, error)
                quote = None
            else:
                return redirect('rental_confirmation', pk=rental.pk)
    return render(request, 'rentals/form.html', {'vehicle': vehicle, 'form': form, 'quote': quote})


@login_required
def rental_list(request):
    rentals = RentalRequest.objects.filter(user=request.user).select_related('vehicle')
    return render(request, 'rentals/list.html', {'rentals': rentals})


@login_required
def rental_confirmation(request, pk):
    rental = get_object_or_404(RentalRequest.objects.select_related('vehicle'), pk=pk, user=request.user)
    return render(request, 'rentals/confirmation.html', {'rental': rental})
