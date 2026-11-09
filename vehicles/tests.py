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


class CatalogPhotosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('load_demo', stdout=StringIO())

    def test_combined_filters_and_price_boundary(self):
        response = self.client.get(reverse('vehicle_list'), {
            'categoria': 'sedan', 'marca': 'Toyota', 'transmision': 'automatica',
            'pasajeros': '5', 'precio_max': '950.00'})
        self.assertEqual([v.model for v in response.context['vehicles']], ['Corolla'])
        self.assertFalse(self.client.get(reverse('vehicle_list'), {
            'marca': 'Toyota', 'precio_max': '949.99'}).context['vehicles'].exists())

    def test_availability_and_sorting(self):
        Vehicle.objects.filter(brand='Toyota').update(available=False)
        response = self.client.get(reverse('vehicle_list'), {'disponibles': 'on', 'orden': 'precio_desc'})
        prices = [v.daily_price for v in response.context['vehicles']]
        self.assertEqual(prices, sorted(prices, reverse=True))
        self.assertNotIn('Toyota', [v.brand for v in response.context['vehicles']])
        self.assertEqual(len(prices), 5)

    def test_invalid_filters_are_visible_without_server_error(self):
        for data in [{'precio_max': '-10'}, {'precio_max': 'no'}, {'pasajeros': '99'},
                {'marca': 'inexistente'}, {'orden': 'daily_price;DROP TABLE vehicles'}]:
            response = self.client.get(reverse('vehicle_list'), data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['filter_form'].errors)
            self.assertFalse(response.context['vehicles'].exists())
        self.assertEqual(Vehicle.objects.count(), 6)

    def test_photo_loader_preserves_existing_images_and_is_repeatable(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        vehicle = Vehicle.objects.first()
        vehicle.image = 'vehicles/personal.jpg'
        vehicle.save(update_fields=['image'])
        with TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            call_command('load_vehicle_images', stdout=StringIO())
            first = list(Vehicle.objects.values_list('image', flat=True))
            call_command('load_vehicle_images', stdout=StringIO())
            self.assertEqual(first, list(Vehicle.objects.values_list('image', flat=True)))
            self.assertEqual(len(list(Path(directory).rglob('*.jpg'))), 5)
            vehicle.refresh_from_db()
            self.assertEqual(vehicle.image.name, 'vehicles/personal.jpg')
            for other in Vehicle.objects.exclude(pk=vehicle.pk):
                self.assertTrue(other.image.storage.exists(other.image.name))

    def test_image_can_be_uploaded_through_admin_and_rendered(self):
        from tempfile import TemporaryDirectory
        from django.conf import settings
        from django.core.files.uploadedfile import SimpleUploadedFile
        user = User.objects.create_superuser('photo_admin', 'photo@example.test', 'PhotoTest!234')
        self.client.force_login(user)
        vehicle = Vehicle.objects.first()
        data = {'brand': vehicle.brand, 'model': vehicle.model, 'year': vehicle.year,
            'category': vehicle.category, 'daily_price': vehicle.daily_price,
            'passengers': vehicle.passengers, 'transmission': vehicle.transmission,
            'description': vehicle.description, 'available': 'on', '_save': 'Guardar'}
        content = (settings.BASE_DIR / 'static/catalog/nissan-march.jpg').read_bytes()
        data['image'] = SimpleUploadedFile('my-car.jpg', content, content_type='image/jpeg')
        with TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            response = self.client.post(reverse('admin:vehicles_vehicle_change', args=[vehicle.pk]), data)
            self.assertEqual(response.status_code, 302)
            vehicle.refresh_from_db()
            self.assertTrue(vehicle.image.storage.exists(vehicle.image.name))
            self.assertContains(self.client.get(reverse('vehicle_detail', args=[vehicle.pk])), vehicle.image.url)

    def test_photo_credits_are_public_and_complete(self):
        response = self.client.get(reverse('image_credits'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['photos']), 6)
        self.assertContains(response, 'CC BY-SA 4.0')
        self.assertContains(response, 'Bull-Doser')
