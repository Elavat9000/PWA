from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Vehicle(models.Model):
    class Category(models.TextChoices):
        COMPACT = 'compacto', 'Compacto'
        SEDAN = 'sedan', 'Sedán'
        SUV = 'suv', 'SUV'

    class Transmission(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        AUTOMATIC = 'automatica', 'Automática'

    brand = models.CharField('marca', max_length=60)
    model = models.CharField('modelo', max_length=80)
    year = models.PositiveSmallIntegerField('año', validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    category = models.CharField('categoría', max_length=20, choices=Category.choices)
    daily_price = models.DecimalField('precio diario', max_digits=9, decimal_places=2, validators=[MinValueValidator(1)])
    passengers = models.PositiveSmallIntegerField('pasajeros', validators=[MinValueValidator(1), MaxValueValidator(20)])
    transmission = models.CharField('transmisión', max_length=20, choices=Transmission.choices)
    description = models.TextField('descripción')
    image = models.ImageField('imagen', upload_to='vehicles/', blank=True)
    available = models.BooleanField('disponible', default=True)

    class Meta:
        ordering = ['brand', 'model', 'year']
        verbose_name = 'vehículo'
        verbose_name_plural = 'vehículos'
        constraints = [
            models.CheckConstraint(condition=models.Q(daily_price__gte=1), name='vehicle_positive_price'),
            models.CheckConstraint(condition=models.Q(passengers__gte=1, passengers__lte=20), name='vehicle_passenger_range'),
        ]

    def __str__(self):
        return f'{self.brand} {self.model} {self.year}'

# Create your models here.
