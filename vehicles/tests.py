from io import StringIO
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Vehicle


class VehicleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('load_demo', stdout=StringIO())

    def test_demo_is_repeatable_and_preserves_edits(self):
        vehicle = Vehicle.objects.first()
        vehicle.daily_price = Decimal('800.00')
        vehicle.available = False
        vehicle.save()
        call_command('load_demo', stdout=StringIO())
        self.assertEqual(Vehicle.objects.count(), 6)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.daily_price, Decimal('800.00'))
        self.assertFalse(vehicle.available)

    def test_catalog_detail_and_filter(self):
        response = self.client.get(reverse('vehicle_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['vehicles']), 6)
        for vehicle in Vehicle.objects.all():
            self.assertContains(response, f'{vehicle.brand} {vehicle.model}')
            self.assertContains(self.client.get(reverse('vehicle_detail', args=[vehicle.pk])), vehicle.description)
        response = self.client.get(reverse('vehicle_list'), {'categoria': 'suv'})
        self.assertEqual(len(response.context['vehicles']), 2)
        self.assertTrue(all(v.category == 'suv' for v in response.context['vehicles']))

    def test_empty_category_missing_detail_and_unavailable(self):
        self.assertContains(self.client.get(reverse('vehicle_list'), {'categoria': 'inexistente'}), 'No hay vehículos')
        self.assertEqual(self.client.get(reverse('vehicle_detail', args=[9999])).status_code, 404)
        vehicle = Vehicle.objects.first()
        vehicle.available = False
        vehicle.save()
        self.assertContains(self.client.get(reverse('vehicle_detail', args=[vehicle.pk])), 'No disponible')

    def test_invalid_price_and_passengers(self):
        vehicle = Vehicle.objects.first()
        for field, value in [('daily_price', -1), ('passengers', 0), ('year', 1800)]:
            original = getattr(vehicle, field)
            setattr(vehicle, field, value)
            with self.assertRaises(ValidationError):
                vehicle.full_clean()
            setattr(vehicle, field, original)

    def test_admin_crud_and_normal_user_denied(self):
        normal = User.objects.create_user('normal', password='Prueba!23456')
        self.client.force_login(normal)
        url = reverse('admin:vehicles_vehicle_changelist')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.post(reverse('admin:vehicles_vehicle_add'), {}).status_code, 302)
        admin = User.objects.create_superuser('admin', 'admin@example.test', 'Prueba!23456')
        self.client.force_login(admin)
        self.assertEqual(self.client.get(url).status_code, 200)
        data = {'brand': 'Prueba', 'model': 'Demo', 'year': 2026, 'category': 'suv',
                'daily_price': '900.00', 'passengers': 5, 'transmission': 'manual',
                'description': 'Vehículo de prueba', 'available': 'on', '_save': 'Guardar'}
        self.assertEqual(self.client.post(reverse('admin:vehicles_vehicle_add'), data).status_code, 302)
        vehicle = Vehicle.objects.get(brand='Prueba')
        data['model'] = 'Actualizado'
        self.assertEqual(self.client.post(reverse('admin:vehicles_vehicle_change', args=[vehicle.pk]), data).status_code, 302)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.model, 'Actualizado')
        self.assertEqual(self.client.post(reverse('admin:vehicles_vehicle_delete', args=[vehicle.pk]), {'post': 'yes'}).status_code, 302)
        self.assertFalse(Vehicle.objects.filter(pk=vehicle.pk).exists())
