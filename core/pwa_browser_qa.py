"""QA opcional de catálogo sin conexión: base y fotografías temporales."""
from io import StringIO
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import override_settings
from django.urls import re_path
from django.views.static import serve

from config.urls import urlpatterns as project_patterns
from rentals.models import RentalRequest
from vehicles.models import Vehicle


def images(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [re_path(r'^media/(?P<path>.*)$', images), *project_patterns]


@override_settings(ROOT_URLCONF='core.pwa_browser_qa')
class OfflineBrowserTests(StaticLiveServerTestCase):
    def test_full_public_catalogue_and_private_exclusions(self):
        output = Path(tempfile.mkdtemp(prefix='DriveSmart_offline_'))
        with override_settings(MEDIA_ROOT=output / 'media'):
            call_command('load_demo', stdout=StringIO())
            call_command('load_faq', stdout=StringIO())
            call_command('load_vehicle_images', stdout=StringIO())
            password = secrets.token_urlsafe(24)
            get_user_model().objects.create_user('PRIVATE_OFFLINE_MARKER', password=password)
            target = Vehicle.objects.get(brand='Toyota', model='Corolla')
            fixture = output / 'fixture.json'
            fixture.write_text(json.dumps({'base': self.live_server_url, 'output': str(output),
                'vehicle': target.pk, 'password': password}), encoding='utf-8')
            result = subprocess.run(['node', str(settings.BASE_DIR / 'core/qa/offline.mjs'), str(fixture)],
                cwd=settings.BASE_DIR, capture_output=True, text=True, encoding='utf-8', timeout=180)
            (output / 'process.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
            print('Evidencias offline: ' + str(output))
            print(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(RentalRequest.objects.exists())
