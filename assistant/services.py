"""Respuestas locales: conocimiento revisado y filtros explícitos del catálogo real."""
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher, get_close_matches
import hashlib
import re
import unicodedata

from django.urls import reverse

from vehicles.models import Vehicle
from .models import KnowledgeEntry


UNKNOWN_REPLY = ('No tengo información suficiente para responder esa pregunta. '
                 'La registraré para que el administrador pueda revisarla.')

SYNONYMS = {
    'auto': 'vehiculo', 'autos': 'vehiculo', 'coche': 'vehiculo', 'coches': 'vehiculo',
    'carro': 'vehiculo', 'carros': 'vehiculo', 'automovil': 'vehiculo',
    'automoviles': 'vehiculo', 'vehiculos': 'vehiculo',
    'camioneta': 'suv', 'camionetas': 'suv', 'suvs': 'suv',
    'compactos': 'compacto', 'sedanes': 'sedan',
    'rentar': 'solicitar renta', 'alquilar': 'solicitar renta',
    'alquilo': 'solicitar renta', 'arrendar': 'solicitar renta',
    'rentas': 'renta', 'solicito': 'solicitar', 'solicitudes': 'solicitud',
    'economico': 'barato', 'economicos': 'barato', 'economica': 'barato',
    'economicas': 'barato', 'baratos': 'barato', 'barata': 'barato', 'baratas': 'barato',
    'automatica': 'automatico', 'automaticos': 'automatico', 'automaticas': 'automatico',
    'manuales': 'manual', 'costo': 'precio', 'costos': 'precio', 'precios': 'precio',
    'tarifa': 'precio', 'tarifas': 'precio', 'cuesta': 'precio', 'cuestan': 'precio',
    'registrarme': 'registro', 'registrarse': 'registro', 'registrar': 'registro',
    'consulto': 'consultar', 'veo': 'consultar', 'ver': 'consultar',
    'pagar': 'pago', 'pagos': 'pago', 'incluyen': 'incluye', 'incluido': 'incluye',
    'disponibles': 'disponible', 'pasajero': 'pasajeros', 'persona': 'personas',
}
COMMON_WORDS = set('como donde cuanto cuales cual que el la los las un una unos unas y o '
                   'de del a al en con por para puedo puede tienen tiene hay me mi mis se es son '
                   'su sus esta estan tengo favor quisiera busco necesito realizar'.split())
# Estos términos nunca se descartan al comparar preguntas.
QUALIFIERS = {'no', 'sin', 'antes', 'despues', 'amplia', 'limitada', 'gratis', 'gratuito'}


def plain_text(text):
    return ''.join(char for char in unicodedata.normalize('NFKD', text.lower())
                   if not unicodedata.combining(char))


def normalize_text(text):
    words = re.sub(r'[^\w\s]', ' ', plain_text(text)).split()
    normalized = []
    for word in words:
        if word not in SYNONYMS and len(word) >= 5:
            similar = get_close_matches(word, SYNONYMS, n=1, cutoff=0.90)
            if similar:
                word = similar[0]
        normalized.extend(SYNONYMS.get(word, word).split())
    return ' '.join(normalized)


def question_key(text):
    return hashlib.sha256(normalize_text(text).encode('utf-8')).hexdigest()


def content_words(text):
    words = set(normalize_text(text).split()) - COMMON_WORDS - {'vehiculo'}
    if {'calcula', 'precio'} <= words:
        words.discard('renta')
    return words


def matching_entry(question, entries):
    """Exigir contenido casi idéntico; compartir palabras genéricas no basta."""
    query = content_words(question)
    if not query:
        return None
    matches = []
    exact_key = question_key(question)
    for entry in entries:
        if entry.question_key == exact_key:
            return entry
        candidate = content_words(entry.question)
        if not candidate or query & QUALIFIERS != candidate & QUALIFIERS:
            continue
        shared = len(query & candidate)
        coverage = shared / max(len(query), len(candidate))
        ratio = SequenceMatcher(None, ' '.join(sorted(query)), ' '.join(sorted(candidate))).ratio()
        if query == candidate or (len(query) == len(candidate) and shared >= 2 and coverage >= 0.8 and ratio >= 0.9):
            matches.append((ratio, entry))
    if not matches:
        return None
    matches.sort(key=lambda match: match[0], reverse=True)
    # Si dos respuestas distintas compiten, pedir revisión en vez de elegir al azar.
    if (len(matches) > 1 and matches[0][1].status == KnowledgeEntry.Status.PUBLISHED
            and matches[0][1].answer != matches[1][1].answer):
        return None
    return matches[0][1]


def amount(text):
    if ',' in text and '.' not in text and len(text.rsplit(',', 1)[1]) == 2:
        text = text.replace(',', '.')
    else:
        text = text.replace(',', '')
    return Decimal(text)


def vehicle_reply(question):
    text = normalize_text(question)
    words = set(text.split())
    if words & {'no', 'sin'}:
        return None
    brands = [brand for brand in Vehicle.objects.order_by('brand').values_list('brand', flat=True).distinct()
              if re.search(r'\b' + re.escape(normalize_text(brand)) + r'\b', text)]
    models = [model for model in Vehicle.objects.order_by('model').values_list('model', flat=True).distinct()
              if re.search(r'\b' + re.escape(normalize_text(model)) + r'\b', text)]
    categories = words & {'compacto', 'sedan', 'suv'}
    transmissions = words & {'automatico', 'manual'}
    if not (brands or models or categories or transmissions or words & {'vehiculo', 'disponible', 'barato'}):
        return None
    if any(len(filters) > 1 for filters in (brands, models, categories, transmissions)):
        return None

    vehicles = Vehicle.objects.all()
    remaining = plain_text(question)
    passenger_pattern = r'\b(?:para\s+)?(\d{1,2})\s+(?:personas?|pasajeros?|plazas)\b'
    passenger_matches = list(re.finditer(passenger_pattern, remaining))
    if len(passenger_matches) > 1:
        return None
    if passenger_matches:
        vehicles = vehicles.filter(passengers__gte=int(passenger_matches[0][1]))
        remaining = re.sub(passenger_pattern, ' ', remaining)

    number = r'(\d[\d,.]*)'
    price_pattern = rf'\b(hasta|maximo|menos de|por debajo de|desde|al menos)\s+\$?\s*{number}'
    prices = list(re.finditer(price_pattern, remaining))
    for price in prices:
        lookup = {'menos de': 'lt', 'por debajo de': 'lt', 'desde': 'gte', 'al menos': 'gte'}.get(price[1], 'lte')
        try:
            vehicles = vehicles.filter(**{f'daily_price__{lookup}': amount(price[2].rstrip('.,'))})
        except InvalidOperation:
            return None
    remaining = re.sub(price_pattern, ' ', remaining)

    names = set(normalize_text(' '.join(brands + models)).split())
    allowed = COMMON_WORDS | names | {'vehiculo', 'disponible', 'barato', 'precio', 'mas',
                                     'automatico', 'manual', 'compacto', 'sedan', 'suv',
                                     'opciones', 'catalogo', 'mostrar', 'muestra', 'diario', 'dia', 'mxn', 'pesos'}
    unrecognized = set(normalize_text(remaining).split()) - allowed
    if unrecognized:
        # No ignorar condiciones desconocidas como seguro, combustible o entrega.
        return None
    if brands:
        vehicles = vehicles.filter(brand=brands[0])
    if models:
        vehicles = vehicles.filter(model=models[0])
    if categories:
        vehicles = vehicles.filter(category=next(iter(categories)))
    if transmissions:
        transmission = 'automatica' if 'automatico' in transmissions else 'manual'
        vehicles = vehicles.filter(transmission=transmission)
    # Consultar el precio de uno identificado puede mostrar también su estado no disponible.
    if not (words & {'precio'} and (brands or models)):
        vehicles = vehicles.filter(available=True)
    vehicles = vehicles.order_by('daily_price', 'pk')[:3]
    results = [{
        'id': vehicle.pk, 'name': str(vehicle), 'daily_price': str(vehicle.daily_price),
        'passengers': vehicle.passengers, 'transmission': vehicle.get_transmission_display(),
        'available': vehicle.available, 'url': reverse('vehicle_detail', args=[vehicle.pk]),
    } for vehicle in vehicles]
    reply = ('Estas opciones del catálogo cumplen los filtros indicados. '
             'La disponibilidad por fechas se comprueba al solicitar renta.' if results else
             'No encontré vehículos del catálogo que cumplan esas condiciones.')
    return {'reply': reply, 'vehicles': results, 'source': 'vehicles'}


def answer_question(question, user=None, context=None):
    """Único punto de entrada para las vistas; no genera respuestas ni cambia rentas."""
    from .conversation import contextual_reply

    memory = context if isinstance(context, dict) else {}
    sensitive = plain_text(question)
    if (re.search(r'\b(?:contrasena|password|clave|token|numero de tarjeta|numero de licencia|telefono|correo)\s*(?:es|:|=)\s*\S+', sensitive)
            or re.search(r'\b\d{10,19}\b|[\w.+-]+@[\w.-]+\.[a-z]{2,}', sensitive)):
        memory.clear()
        return {'reply': 'Evita compartir contraseñas, documentos o datos de contacto. No registraré ese mensaje. Reformula tu consulta sin datos personales.',
                'vehicles': [], 'source': 'privacy'}
    inventory = contextual_reply(question, memory)
    if inventory is not None:
        return inventory
    memory.clear()
    inventory = vehicle_reply(question)
    if inventory is not None:
        return inventory
    published = KnowledgeEntry.objects.filter(status=KnowledgeEntry.Status.PUBLISHED).exclude(answer='')
    entry = matching_entry(question, published)
    if entry:
        return {'reply': entry.answer, 'vehicles': [], 'source': 'knowledge'}
    pending = KnowledgeEntry.objects.filter(status=KnowledgeEntry.Status.PENDING)
    if matching_entry(question, pending) is None:
        KnowledgeEntry.objects.get_or_create(
            question_key=question_key(question),
            defaults={'question': question, 'asked_by': user if user and user.is_authenticated else None},
        )
    return {'reply': UNKNOWN_REPLY, 'vehicles': [], 'source': 'pending'}
