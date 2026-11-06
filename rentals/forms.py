from django import forms
from django.utils import timezone

from .models import RentalRequest


class RentalRequestForm(forms.ModelForm):
    class Meta:
        model = RentalRequest
        fields = ('start_date', 'end_date')
        widgets = {
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['min'] = timezone.localdate().isoformat()
