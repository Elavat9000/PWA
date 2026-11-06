from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'category', 'daily_price', 'available')
    list_filter = ('category', 'transmission', 'available')
    search_fields = ('brand', 'model')
    list_editable = ('available',)

# Register your models here.
