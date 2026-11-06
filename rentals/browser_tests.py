"""QA opcional: python manage.py test rentals.browser_tests --verbosity 2.

Requiere Node/Playwright de desarrollo. StaticLiveServerTestCase aísla los datos.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
import secrets
import subprocess

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone

from vehicles.models import Vehicle
from .models import RentalRequest


class RentalBrowserTests(StaticLiveServerTestCase):
    def test_desktop_and_mobile_rental_flow(self):
        call_command('load_demo', verbosity=0)
        password = secrets.token_urlsafe(24)
        users = get_user_model()
        users.objects.create_user('qa_renter', password=password)
        users.objects.create_user('qa_other', password=password)
        users.objects.create_superuser('qa_admin', 'qa@example.test', password)
        vehicle = Vehicle.objects.first()
        vehicle.daily_price = '750.25'
        vehicle.save()
        unavailable = Vehicle.objects.exclude(pk=vehicle.pk).first()
        unavailable.available = False
        unavailable.save()
        start = timezone.localdate() + timedelta(days=10)
        output = Path(settings.BASE_DIR) / 'test-results' / datetime.now().strftime('phase3-browser-%Y%m%d-%H%M%S-%f')
        output.mkdir(parents=True)
        fixture = output / 'fixture.json'
        fixture.write_text(json.dumps({
            'base': self.live_server_url, 'password': password, 'vehicle': vehicle.pk,
            'unavailable': unavailable.pk, 'start': start.isoformat(),
            'end': (start + timedelta(days=3)).isoformat(),
            'next_end': (start + timedelta(days=5)).isoformat(), 'output': str(output),
        }), encoding='utf-8')
        result = subprocess.run(['node', 'scripts/rentals_qa.mjs', str(fixture)],
                                cwd=settings.BASE_DIR, capture_output=True, text=True,
                                encoding='utf-8', timeout=120)
        (output / 'process.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        print(result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(RentalRequest.objects.count(), 3)
        for status in RentalRequest.Status.values:
            self.assertEqual(RentalRequest.objects.filter(status=status).count(), 1)
