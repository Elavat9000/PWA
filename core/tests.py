from django.test import TestCase
from django.conf import settings
from django.urls import reverse
from PIL import Image
import json


class PrivacyCacheTests(TestCase):
    def test_private_dynamic_page_not_stored_by_http_cache(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user('cache_test', password='TestOnly!1839')
        self.client.force_login(user)
        response = self.client.get('/mis-rentas/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response.headers.get('Cache-Control', ''))

    def test_public_dynamic_pages_and_chat_are_not_stored(self):
        for name in ('home', 'login', 'signup', 'vehicle_list'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertIn('no-store', response.headers['Cache-Control'])
        response = self.client.post(reverse('assistant_chat'), '{}', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('no-store', response.headers['Cache-Control'])


class PwaTests(TestCase):
    def test_manifest_fields(self):
        response = self.client.get(reverse('pwa_manifest'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/manifest+json')
        data = json.loads(b''.join(response.streaming_content))
        for key, value in {'name': 'DriveSmart', 'short_name': 'DriveSmart', 'start_url': '/',
                           'scope': '/', 'display': 'standalone', 'theme_color': '#17604e',
                           'background_color': '#f6f5ef'}.items():
            self.assertEqual(data[key], value)
        self.assertEqual({icon['sizes'] for icon in data['icons']}, {'192x192', '512x512'})

    def test_local_png_icons_dimensions(self):
        for size in (192, 512):
            with Image.open(settings.BASE_DIR / 'static/pwa/icons' / f'icon-{size}.png') as image:
                self.assertEqual(image.format, 'PNG')
                self.assertEqual(image.size, (size, size))
                image.verify()

    def test_root_worker_headers_and_cache_allowlist(self):
        response = self.client.get(reverse('pwa_service_worker'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Service-Worker-Allowed'], '/')
        self.assertEqual(response.headers['Content-Type'], 'application/javascript')
        self.assertEqual(response.headers['Cache-Control'], 'no-cache')
        source = b''.join(response.streaming_content).decode()
        self.assertIn("const CACHE_PREFIX = 'drivesmart-public-';", source)
        self.assertIn("request.method !== 'GET'", source)
        self.assertIn("cache: 'no-store'", source)
        for private_path in ('/admin/', '/mis-rentas/', '/cuentas/', '/rentas/', '/asistente/consultar/'):
            self.assertNotIn(f"'{private_path}'", source.split('];', 1)[0])

    def test_offline_page_is_static_and_informative(self):
        response = self.client.get(reverse('pwa_offline'))
        self.assertEqual(response.status_code, 200)
        html = b''.join(response.streaming_content).decode()
        self.assertIn('Necesitas conexión a internet para verificar fechas y disponibilidad', html)
        self.assertNotIn('csrfmiddlewaretoken', html)
        self.assertNotIn('assistant-panel', html)
        self.assertNotIn('sessionid', response.cookies)

    def test_template_registers_manifest_and_worker_script(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'rel="manifest"')
        self.assertContains(response, '/manifest.webmanifest')
        self.assertContains(response, '/static/js/pwa.js')

    def test_delivery_allowlist_excludes_local_files(self):
        from scripts.package_beta import collect_files
        paths = {path.relative_to(settings.BASE_DIR).as_posix() for path in collect_files(settings.BASE_DIR)}
        self.assertTrue({'manage.py', 'requirements.txt', 'INSTRUCTIONS.txt', '.env.example',
                         'assistant/migrations/0001_initial.py', 'static/images/suv.svg',
                         'static/pwa/icons/icon-192.png', 'static/pwa/icons/icon-512.png'} <= paths)
        for path in paths:
            self.assertNotIn(path.split('/')[0], {'.git', '.agents', '.venv', 'node_modules', 'test-results', 'media'})
            self.assertFalse(path.endswith(('.sqlite3', '.sqlite', '.db', '.pyc', '.log', '.zip', '.pem', '.key')))
            self.assertNotEqual(path, '.env')
