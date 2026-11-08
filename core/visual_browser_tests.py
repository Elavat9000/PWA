"""QA visual opcional: manage.py test core.visual_browser_tests --verbosity 2."""
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


class VisualBrowserTests(StaticLiveServerTestCase):
    def test_responsive_screens_and_style_cache_upgrade(self):
        call_command('load_demo', stdout=StringIO())
        call_command('load_faq', stdout=StringIO())
        password = secrets.token_urlsafe(24)
        user = get_user_model().objects.create_user('visual_user', password=password)
        vehicle = Vehicle.objects.get(brand='Toyota', model='Corolla')
        start = timezone.localdate() + timedelta(days=30)
        end = start + timedelta(days=3)
        rental = RentalRequest.objects.create(
            user=user, vehicle=vehicle, start_date=start, end_date=end)
        output = Path(settings.BASE_DIR) / 'test-results' / datetime.now().strftime(
            'visual-browser-%Y%m%d-%H%M%S')
        output.mkdir(parents=True)
        fixture = output / 'fixture.json'
        fixture.write_text(json.dumps({
            'base': self.live_server_url, 'output': str(output),
            'password': password, 'vehicle': vehicle.pk, 'rental': rental.pk,
            'start': str(start), 'end': str(end),
        }), encoding='utf-8')
        result = subprocess.run(
            ['node', 'scripts/visual_qa.mjs', str(fixture)], cwd=settings.BASE_DIR,
            capture_output=True, text=True, encoding='utf-8', timeout=240)
        (output / 'process.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
