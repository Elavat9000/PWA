from django import forms
from .models import Vehicle


class CatalogFilterForm(forms.Form):
    categoria = forms.ChoiceField(label='Categoría', required=False,
        choices=[('', 'Todas las categorías'), *Vehicle.Category.choices])
    marca = forms.ChoiceField(label='Marca', required=False)
    transmision = forms.ChoiceField(label='Transmisión', required=False,
        choices=[('', 'Cualquiera'), *Vehicle.Transmission.choices])
    pasajeros = forms.IntegerField(label='Pasajeros (mínimo)', required=False, min_value=1, max_value=20)
    precio_max = forms.DecimalField(label='Precio máximo por día (MXN)', required=False,
        min_value=1, max_digits=9, decimal_places=2)
    disponibles = forms.BooleanField(label='Solo disponibles en catálogo', required=False)
    orden = forms.ChoiceField(label='Ordenar por', required=False, choices=[
        ('', 'Marca y modelo'), ('precio_asc', 'Menor precio'), ('precio_desc', 'Mayor precio')])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        brands = Vehicle.objects.order_by('brand').values_list('brand', flat=True).distinct()
        self.fields['marca'].choices = [('', 'Todas las marcas'), *((brand, brand) for brand in brands)]
        # Conservar el identificador existente del filtro de categoría.
        self.fields['categoria'].widget.attrs['id'] = 'categoria'
