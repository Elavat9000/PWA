"""QA PWA opcional: python manage.py test core.browser_tests --verbosity 2."""
from datetime import datetime, timedelta
from io import StringIO
import json
from pathlib import Path
import secrets
import subprocess

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.utils import timezone

from rentals.models import RentalRequest
from vehicles.models import Vehicle


class PwaBrowserTests(StaticLiveServerTestCase):
    def test_online_offline_cache_and_user_isolation(self):
        call_command('load_demo', stdout=StringIO())
        call_command('load_faq', stdout=StringIO())
        password = secrets.token_urlsafe(24)
        users = get_user_model()
        first = users.objects.create_user('qa_pwa_one', password=password)
        second = users.objects.create_user('qa_pwa_two', password=password)
        users.objects.create_superuser('qa_pwa_admin', 'pwa@example.test', password)
        vehicle = Vehicle.objects.get(brand='Toyota', model='Corolla')
        start = timezone.localdate() + timedelta(days=10)
        rentals = [RentalRequest.objects.create(user=user, vehicle=vehicle,
                   start_date=start, end_date=start + timedelta(days=3)) for user in (first, second)]
        output = Path(settings.BASE_DIR) / 'test-results' / datetime.now().strftime('phase5-browser-%Y%m%d-%H%M%S-%f')
        output.mkdir(parents=True)
        fixture = output / 'fixture.json'
        fixture.write_text(json.dumps({'base': self.live_server_url, 'output': str(output),
            'password': password, 'first': rentals[0].pk, 'second': rentals[1].pk,
            'vehicle': vehicle.pk, 'price': str(vehicle.daily_price)}), encoding='utf-8')
        run = subprocess.run(['node', 'scripts/pwa_qa.mjs', str(fixture)], cwd=settings.BASE_DIR,
                             capture_output=True, text=True, encoding='utf-8', timeout=150)
        (output / 'process.txt').write_text(run.stdout + run.stderr, encoding='utf-8')
        print(run.stdout)
        self.assertEqual(run.returncode, 0, run.stderr)
