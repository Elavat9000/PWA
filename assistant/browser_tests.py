"""QA opcional: python manage.py test assistant.browser_tests --verbosity 2."""
from datetime import datetime
from io import StringIO
import json
from pathlib import Path
import secrets
import subprocess

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command

from vehicles.models import Vehicle
from .models import KnowledgeEntry


class AssistantBrowserTests(StaticLiveServerTestCase):
    def test_learning_desktop_and_mobile(self):
        call_command('load_demo', stdout=StringIO())
        call_command('load_faq', stdout=StringIO())
        password = secrets.token_urlsafe(24)
        users = get_user_model()
        users.objects.create_user('qa_chat_user', password=password)
        users.objects.create_superuser('qa_chat_admin', 'chat@example.test', password)
        vehicle = Vehicle.objects.get(brand='Toyota', model='Corolla')
        output = Path(settings.BASE_DIR) / 'test-results' / datetime.now().strftime('phase4-browser-%Y%m%d-%H%M%S-%f')
        output.mkdir(parents=True)
        fixture = output / 'fixture.json'
        fixture.write_text(json.dumps({
            'base': self.live_server_url, 'password': password, 'output': str(output),
            'vehicle': vehicle.pk, 'price': str(vehicle.daily_price),
        }), encoding='utf-8')
        result = subprocess.run(['node', 'scripts/assistant_qa.mjs', str(fixture)],
                                cwd=settings.BASE_DIR, capture_output=True, text=True,
                                encoding='utf-8', timeout=120)
        (output / 'process.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        print(result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr)
        published = KnowledgeEntry.objects.get(question='¿Los vehículos incluyen seguro de cobertura amplia?')
        self.assertEqual(published.status, KnowledgeEntry.Status.PUBLISHED)
        self.assertEqual(published.answer, 'Respuesta revisada por el administrador de esta prueba local.')
        self.assertEqual(KnowledgeEntry.objects.filter(status=KnowledgeEntry.Status.PUBLISHED).count(), 9)
        self.assertEqual(KnowledgeEntry.objects.filter(status=KnowledgeEntry.Status.PENDING).count(), 2)
