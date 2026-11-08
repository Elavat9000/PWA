"""QA opcional con Playwright convencional; servidor y base temporales.

El módulo Playwright se resuelve con DRIVESMART_PLAYWRIGHT_MODULE, sin añadir
dependencias de ejecución. Evidencias fuera del proyecto, en TEMP.
"""
from datetime import timedelta
from decimal import Decimal
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import tempfile

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.utils import timezone

from vehicles.models import Vehicle
from .models import KnowledgeEntry


class ChatBrowserTests(StaticLiveServerTestCase):
    def test_chat_conversation_responsive_and_pwa(self):
        call_command('load_faq', stdout=StringIO())
        for brand, model, category, passengers, price in (
            ('Toyota', 'Corolla', 'sedan', 5, '750.25'),
            ('Kia', 'Seltos', 'suv', 5, '900.50'),
            ('Mazda', 'CX-5', 'suv', 7, '1400.00'),
        ):
            Vehicle.objects.create(brand=brand, model=model, year=2026, category=category,
                passengers=passengers, transmission='automatica', daily_price=Decimal(price),
                description='Solo prueba temporal.')
        output = Path(tempfile.mkdtemp(prefix='DriveSmart_chat2_'))
        start = timezone.localdate() + timedelta(days=10)
        fixture = output / 'fixture.json'
        fixture.write_text(json.dumps({'base': self.live_server_url, 'output': str(output),
            'start': start.isoformat(), 'end': (start + timedelta(days=3)).isoformat()}), encoding='utf-8')
        result = subprocess.run(['node', str(settings.BASE_DIR / 'assistant/qa/chat.mjs'), str(fixture)],
            cwd=settings.BASE_DIR, capture_output=True, text=True, encoding='utf-8', timeout=180,
            env=os.environ.copy())
        (output / 'process.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        print(f'Evidencias Chat 2.0: {output}')
        print(result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(KnowledgeEntry.objects.filter(question__icontains='cobertura').count(), 1)
