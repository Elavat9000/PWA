from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class RentalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDIENTE', 'Pendiente'
        APPROVED = 'APROBADA', 'Aprobada'
        REJECTED = 'RECHAZADA', 'Rechazada'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='usuario')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.PROTECT, verbose_name='vehículo')
    start_date = models.DateField('fecha de inicio')
    end_date = models.DateField('fecha de devolución')
    daily_price = models.DecimalField('precio diario al solicitar', max_digits=9, decimal_places=2,
                                      editable=False, default=0, validators=[MinValueValidator(1)])
    total_cost = models.DecimalField('costo total', max_digits=16, decimal_places=2,
                                     editable=False, default=0, validators=[MinValueValidator(1)])
    status = models.CharField('estado', max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'solicitud de renta'
        verbose_name_plural = 'solicitudes de renta'
        constraints = [
            models.CheckConstraint(condition=models.Q(end_date__gt=models.F('start_date')),
                                   name='rental_end_after_start'),
            models.CheckConstraint(condition=models.Q(daily_price__gte=1), name='rental_positive_price'),
            models.CheckConstraint(condition=models.Q(total_cost__gte=1), name='rental_positive_total'),
        ]

    def __str__(self):
        return f'Solicitud #{self.pk} · {self.vehicle}'

    @property
    def days(self):
        return (self.end_date - self.start_date).days

    def validate_availability(self):
        """Intervalos [inicio, devolución): una devolución permite iniciar otra renta ese día."""
        if not self.vehicle.available:
            raise ValidationError('Este vehículo no está disponible para solicitar renta.')
        overlapping = RentalRequest.objects.filter(
            vehicle_id=self.vehicle_id,
            status=self.Status.APPROVED,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError('El vehículo ya tiene una renta aprobada que coincide con estas fechas.')

    def clean(self):
        super().clean()
        if not self.start_date or not self.end_date:
            return
        if self.end_date <= self.start_date:
            raise ValidationError({'end_date': 'La devolución debe ser posterior a la fecha de inicio.'})
        if self._state.adding and self.start_date < timezone.localdate():
            raise ValidationError({'start_date': 'La fecha de inicio no puede estar en el pasado.'})
        if self.vehicle_id and (self._state.adding or self.status == self.Status.APPROVED):
            self.validate_availability()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self._state.adding and self.vehicle_id and self.start_date and self.end_date:
                self.daily_price = self.vehicle.daily_price
                self.total_cost = self.daily_price * self.days
            # Se comprueba de nuevo al guardar, además de validar los formularios.
            self.full_clean()
            return super().save(*args, **kwargs)
