import json
from django.conf import settings


def get_reference_photos():
    return json.loads((settings.BASE_DIR / 'static/catalog/credits.json').read_text(encoding='utf-8'))
