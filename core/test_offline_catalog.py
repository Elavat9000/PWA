from decimal import Decimal
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from vehicles.models import Vehicle


class OfflineCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vehicle = Vehicle.objects.create(brand='Toyota', model='Corolla', year=2026,
            category='sedan', transmission='automatica', passengers=5,
            daily_price=Decimal('950.25'), description='Solo prueba temporal.')

    def test_public_snapshot_contains_catalogue_and_warning(self):
        result = self.client.get(reverse('offline_catalog'))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers['X-DriveSmart-Public-Catalog'], '1')
        self.assertEqual(result.headers['Cache-Control'], 'no-cache')
        self.assertContains(result, 'Corolla')
        self.assertContains(result, '950.25')
        self.assertContains(result, 'precio guardado')
        self.assertContains(result, 'verificar los precios actuales, las fechas deseadas y la disponibilidad')
        self.assertContains(result, '/static/images/sedan.svg')

    def test_logged_in_snapshot_has_no_private_content_or_csrf(self):
        user = get_user_model().objects.create_user('PRIVATE_USER_MARKER')
        self.client.force_login(user)
        result = self.client.get(reverse('offline_catalog'))
        for secret in ('PRIVATE_USER_MARKER', 'csrfmiddlewaretoken', 'Cerrar sesión', 'assistant-panel', 'Mis rentas'):
            self.assertNotContains(result, secret)
        self.assertFalse(result.cookies)

    def test_all_records_not_only_first_page_or_available(self):
        for index in range(8):
            Vehicle.objects.create(brand='Prueba', model=f'Modelo {index}', year=2026,
                category='suv', transmission='manual', passengers=7, daily_price=1000,
                description='Temporal', available=index % 2 == 0)
        result = self.client.get(reverse('offline_catalog'))
        self.assertEqual(result.content.decode().count('data-offline-vehicle='), 9)
        self.assertContains(result, 'Modelo 7')
        self.assertContains(result, 'no disponible')

    def test_external_image_is_not_downloadable_by_snapshot(self):
        with patch('django.db.models.fields.files.ImageFieldFile.url', new_callable=lambda: property(lambda self: 'https://external.example/photo.jpg')):
            self.vehicle.image = 'vehicles/test.jpg'
            self.vehicle.save()
            result = self.client.get(reverse('offline_catalog'))
        self.assertContains(result, '/static/images/sedan.svg')
        self.assertNotContains(result, 'https://external.example')

    def test_snapshot_escapes_untrusted_vehicle_text(self):
        self.vehicle.description = '<img src=x onerror=alert(1)>'
        self.vehicle.save()
        result = self.client.get(reverse('offline_catalog'))
        self.assertContains(result, '&lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(result, '<img src=x')

    def test_snapshot_has_no_mutating_post(self):
        self.assertEqual(self.client.post(reverse('offline_catalog')).status_code, 405)

    def test_image_manifest_contains_only_public_photo_paths(self):
        from html.parser import HTMLParser

        class Manifest(HTMLParser):
            reading = False
            data = ''
            def handle_starttag(self, tag, attrs):
                self.reading = tag == 'script' and dict(attrs).get('id') == 'offline-images'
            def handle_data(self, text):
                if self.reading:
                    self.data += text
        parser = Manifest()
        parser.feed(self.client.get(reverse('offline_catalog')).content.decode())
        self.assertEqual(json.loads(parser.data), ['/static/images/sedan.svg'])

    def test_online_pages_still_private_no_store(self):
        for url in ('/', '/vehiculos/', '/cuentas/entrar/'):
            self.assertIn('no-store', self.client.get(url).headers['Cache-Control'])
