"""Contexto corto y consultas de solo lectura. Sin historial ni generación de texto."""
from datetime import date
from decimal import Decimal, InvalidOperation
import re

from django.utils import timezone
from django.urls import reverse

from rentals.models import RentalRequest
from vehicles.models import Vehicle


NUMBERS = dict(zip('uno una dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte treinta'.split(),
                   [1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30]))
MONTHS = {name: index for index, name in enumerate('enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split(), 1)}
DATE_HELP = 'Indica inicio y devolución completos, por ejemplo: del 12/11/2027 al 15/11/2027.'


def response(reply, vehicles=None, source='vehicles', suggestions=None):
    return {'reply': reply, 'vehicles': vehicles or [], 'source': source,
            'suggestions': suggestions or []}


def read_dates(text):
    """Dos fechas explícitas o intervalo con mes escrito. Nunca adivinar días sueltos."""
    pieces = list(re.finditer(r'\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b', text))
    span = None
    dates = []
    try:
        if pieces:
            if len(pieces) != 2:
                return None, text, DATE_HELP
            for piece in pieces:
                value = piece[0]
                if '/' in value:
                    day, month, year = map(int, value.split('/'))
                    dates.append(date(year, month, day))
                else:
                    dates.append(date.fromisoformat(value))
            remaining = text
            for piece in reversed(pieces):
                remaining = remaining[:piece.start()] + ' ' + remaining[piece.end():]
        else:
            span = re.search(r'\b(?:del?\s+)?(\d{1,2})(?:\s+de\s+([a-z]+))?\s+al?\s+(\d{1,2})\s+de\s+([a-z]+)(?:\s+(?:de\s+)?(\d{4}))?\b', text)
            if not span:
                if re.search(r'\b(?:fechas?|noviembre|diciembre|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|hoy|manana)\b|\bdel?\s+\d+\s+al?\s+\d+', text):
                    return None, text, DATE_HELP
                return None, text, None
            first, first_month, last, last_month, year = span.groups()
            if last_month not in MONTHS or (first_month and first_month not in MONTHS):
                return None, text, DATE_HELP
            year = int(year) if year else timezone.localdate().year
            dates = [date(year, MONTHS[first_month or last_month], int(first)),
                     date(year, MONTHS[last_month], int(last))]
            remaining = text[:span.start()] + ' ' + text[span.end():]
        start, end = dates
        if start < timezone.localdate():
            return None, text, 'La fecha de inicio no puede estar en el pasado. ' + DATE_HELP
        if end <= start:
            return None, text, 'La devolución debe ser posterior al inicio. ' + DATE_HELP
        return (start, end), remaining, None
    except ValueError:
        return None, text, 'Esas fechas no son válidas. ' + DATE_HELP


def vehicle_data(vehicle, dates=None):
    return {'id': vehicle.pk, 'name': str(vehicle), 'daily_price': str(vehicle.daily_price),
            'year': vehicle.year, 'category': vehicle.get_category_display(),
            'passengers': vehicle.passengers, 'transmission': vehicle.get_transmission_display(),
            'available': vehicle.available, 'availability_checked': bool(dates),
            'url': reverse('vehicle_detail', args=[vehicle.pk])}


def inventory_query(filters, dates, include_unavailable=False):
    """Consultar de nuevo los datos; nunca persistir precios ni reservas en sesión."""
    vehicles = Vehicle.objects.all()
    lookups = {'brands': 'brand__in', 'models': 'model__in', 'passengers': 'passengers__gte'}
    for key, value in filters.items():
        lookup = 'daily_price__' + key[6:] if key.startswith('price_') else lookups.get(key, key)
        vehicles = vehicles.filter(**{lookup: value})
    if not include_unavailable:
        vehicles = vehicles.filter(available=True)
    if dates:
        # Mismos intervalos [inicio, devolución) y mismo estado que validate_availability.
        blocked = RentalRequest.objects.filter(status=RentalRequest.Status.APPROVED,
            start_date__lt=dates[1], end_date__gt=dates[0]).values('vehicle_id')
        vehicles = vehicles.exclude(pk__in=blocked)
    return vehicles


def contextual_reply(question, context):
    from .services import COMMON_WORDS, amount, normalize_text, plain_text

    raw = plain_text(question)
    # Palabras numéricas solo en capacidad/duración; no alterar nombres de modelos.
    numeric = re.sub(r'\b(' + '|'.join(NUMBERS) + r')(?=\s+(?:personas?|pasajeros?|plazas|dias?)\b)',
                     lambda match: str(NUMBERS[match[0]]), raw)
    text = normalize_text(numeric)
    words = set(text.split())
    names = {}
    for field in ('brand', 'model'):
        names[field] = [value for value in Vehicle.objects.order_by(field).values_list(field, flat=True).distinct()
                        if re.search(r'\b' + re.escape(normalize_text(value)) + r'\b', text)]
    categories = words & {'suv', 'sedan', 'compacto'}
    transmissions = words & {'manual', 'automatico'}
    followup_terms = {'barato', 'grande', 'capacidad', 'otros', 'otro', 'estos', 'esas', 'rentarlo', 'rentarlos', 'ese', 'esa', 'compara', 'comparar', 'diferencia', 'conviene', 'automatico', 'manual', 'dias', 'personas', 'pasajeros', 'plazas', 'hasta', 'desde', 'minimo', 'maximo'}
    vehicle_intent = bool(names['brand'] or names['model'] or categories or transmissions or words & {'vehiculo', 'disponible', 'barato', 'catalogo'})
    date_intent = bool(re.search(r'\d{4}-\d{2}-\d{2}|\d/|\bdel?\s+\d+\s', raw))
    duration_intent = bool(re.search(r'\b\d+\s+dias?\b', numeric))
    if not (vehicle_intent or words & followup_terms or date_intent or duration_intent):
        return None
    # No reinterpretar preguntas de uso del sistema como búsquedas de inventario.
    if words & {'como', 'donde'} and not (names['brand'] or names['model']):
        return None
    compare = bool(words & {'compara', 'comparar', 'comparacion', 'diferencia'})
    new_search = bool(re.search(r'\b(?:busco|necesito|quiero|muestrame|muestra|mostrar|nueva busqueda)\b', text)) and not words & {'otros', 'otro'}
    if names['brand'] or names['model']:
        new_search = True
    selecting_estimate = bool(context.get('awaiting_vehicle') and names['model'] and not re.search(r'\b(?:busco|necesito|quiero|nueva)\b', text))
    state = {} if new_search and not selecting_estimate else dict(context)
    state.pop('awaiting_vehicle', None)
    filters = dict(state.get('filters', {}))
    previous_ids = list(state.get('result_ids', []))[:3]
    dates, remaining, date_error = read_dates(numeric)
    duration_matches = list(re.finditer(r'\b(\d+)\s+dias?\b', remaining))
    passenger_matches = list(re.finditer(r'\b(\d+)\s+(?:personas?|pasajeros?|plazas)\b', remaining))
    price_pattern = r'\b(hasta|maximo|minimo|menos de|por debajo de|desde|al menos)\s+\$?\s*(\d[\d,.]*)'
    prices = list(re.finditer(price_pattern, remaining))
    # Mantener la protección previa: nunca ignorar negaciones o condiciones ajenas al modelo.
    if words & {'no', 'sin'} or len(passenger_matches) > 1:
        return None
    cleaned = re.sub(price_pattern, ' ', remaining)
    cleaned = re.sub(r'\b\d+\s+(?:dias?|personas?|pasajeros?|plazas)\b', ' ', cleaned)
    name_words = set(normalize_text(' '.join(names['brand'] + names['model'])).split())
    allowed = COMMON_WORDS | name_words | set('vehiculo disponible barato precio mas menos automatico manual compacto sedan suv opciones catalogo mostrar muestra muestrame diario dia dias mxn pesos quiero conducir rentarlo rentarlos solicitar renta compara comparar comparacion diferencia estos dos tres esos esas entre otros otro uno algo grande capacidad conviene mejor recomendado presupuesto minimo maximo desde hasta del al fecha fechas el cual cuanto tienen tienes hay vez nueva busqueda ahora nuevo'.split())
    # Incluso con fechas erróneas, no convertir condiciones desconocidas en filtros válidos.
    checked_text = re.sub(r'\b\d+\b', ' ', normalize_text(cleaned)) if date_error else normalize_text(cleaned)
    unknown = set(checked_text.split()) - allowed - (set(MONTHS) | {'hoy', 'manana'} if date_error else set())
    if unknown:
        return None
    if not context and not vehicle_intent and not date_intent and not duration_intent:
        return response('¿Qué vehículo o categoría quieres consultar?', source='clarification')
    if len(categories) > 1 or len(transmissions) > 1 or (not compare and (len(names['brand']) > 1 or len(names['model']) > 1)):
        return response('¿Qué categoría, transmisión o modelo quieres consultar primero?', source='clarification')
    if date_error:
        state.pop('dates', None)
        state.pop('result_ids', None)
        state.pop('selected_id', None)
        context.clear()
        # Conservar filtros explícitos válidos para la corrección de fechas.
        if categories:
            filters['category'] = next(iter(categories))
        if transmissions:
            filters['transmission'] = 'automatica' if 'automatico' in transmissions else 'manual'
        if passenger_matches:
            filters['passengers'] = int(passenger_matches[0][1])
        context.update({'filters': filters})
        return response(date_error, source='clarification')
    if categories:
        filters['category'] = next(iter(categories))
    if transmissions:
        filters['transmission'] = 'automatica' if 'automatico' in transmissions else 'manual'
    if passenger_matches:
        capacity = int(passenger_matches[0][1])
        if not 1 <= capacity <= 20:
            return response('Indica una capacidad entre 1 y 20 pasajeros.', source='clarification')
        filters['passengers'] = capacity
    if names['brand']:
        filters['brands'] = names['brand'][:3]
    if names['model']:
        filters['models'] = names['model'][:3]
    for price in prices:
        try:
            value = amount(price[2].rstrip('.,'))
        except InvalidOperation:
            return response('Indica un presupuesto diario válido en MXN.', source='clarification')
        if not 0 < value <= Decimal('9999999.99'):
            return response('El presupuesto diario debe ser positivo y no superar 9,999,999.99 MXN.', source='clarification')
        lookup = {'menos de': 'lt', 'por debajo de': 'lt', 'desde': 'gte', 'al menos': 'gte', 'minimo': 'gte'}.get(price[1], 'lte')
        filters['price_' + lookup] = str(value)
    if dates:
        state['dates'] = [value.isoformat() for value in dates]
    elif state.get('dates'):
        dates = tuple(date.fromisoformat(value) for value in state['dates'])
        if dates[0] < timezone.localdate():
            context.clear()
            return response('Las fechas de la conversación ya pasaron. ' + DATE_HELP, source='clarification')
    if duration_matches:
        if len(duration_matches) != 1 or not 1 <= int(duration_matches[0][1]) <= 3650:
            return response('Indica una duración de entre 1 y 3650 días.', source='clarification')
        state['days'] = int(duration_matches[0][1])
    if dates and duration_matches and state['days'] != (dates[1] - dates[0]).days:
        return response('La duración no coincide con esas fechas. Confirma el intervalo o inicia una nueva búsqueda.', source='clarification')
    if dates:
        state['days'] = (dates[1] - dates[0]).days
    prior = list(Vehicle.objects.filter(pk__in=previous_ids).order_by('daily_price', 'pk'))
    if 'grande' in words and prior:
        filters.pop('brands', None)
        filters.pop('models', None)
        filters['passengers'] = max(vehicle.passengers for vehicle in prior) + 1
    if 'barato' in words and words & {'algo', 'uno', 'tienen'} and prior:
        filters.pop('brands', None)
        filters.pop('models', None)
        filters['price_lt'] = str(min(vehicle.daily_price for vehicle in prior))
    if 'conviene' in words or 'mejor' in words:
        context.update(state)
        return response('¿Quieres priorizar el precio más bajo o la mayor capacidad? Solo puedo comparar los datos registrados.', source='clarification', suggestions=['¿Cuál es el más barato?', '¿Cuál tiene más capacidad?'])
    specific_price = 'precio' in words and (names['brand'] or names['model']) and not dates
    vehicles = inventory_query(filters, dates, include_unavailable=specific_price)
    if words & {'otros', 'otro'}:
        vehicles = vehicles.exclude(pk__in=previous_ids)
    if compare and words & {'estos', 'esos', 'dos', 'diferencia'} and previous_ids and not new_search:
        vehicles = vehicles.filter(pk__in=previous_ids)
    if state.get('selected_id') and not new_search and (duration_matches or words & {'rentarlo', 'rentarlos'}):
        vehicles = vehicles.filter(pk=state['selected_id'])
    most_capacity = 'capacidad' in words and 'mas' in words
    ordered = vehicles.order_by('-passengers', 'daily_price', 'pk') if most_capacity else vehicles.order_by('daily_price', 'pk')
    results = list(ordered[:3])
    estimate = bool(duration_matches) or bool('precio' in words and (state.get('days') or words & {'rentarlo', 'rentarlos'})) or selecting_estimate
    cheapest = 'barato' in words and bool(words & {'cual', 'el', 'uno'})
    if (cheapest or most_capacity) and not estimate:
        results = results[:1]
    state['filters'] = filters
    state['result_ids'] = [vehicle.pk for vehicle in results]
    state.pop('selected_id', None)
    if len(results) == 1:
        state['selected_id'] = results[0].pk
    context.clear()
    context.update(state)
    if not results:
        return response('No encontré vehículos que cumplan todas esas condiciones. Puedes iniciar una nueva búsqueda o cambiar un filtro.')
    items = [vehicle_data(vehicle, dates) for vehicle in results]
    date_note = (f'Disponibilidad consultada del {dates[0]:%d/%m/%Y} al {dates[1]:%d/%m/%Y}. '
                 'Las solicitudes pendientes no bloquean fechas; debe comprobarse de nuevo al confirmar.' if dates else
                 'No he comprobado disponibilidad por fechas. ¿Para qué fechas lo necesitas?')
    if estimate:
        if len(results) != 1:
            context['awaiting_vehicle'] = True
            return response('¿Qué vehículo quieres cotizar? Indica su modelo para calcular una estimación.', items,
                            suggestions=[f'Precio del {vehicle.brand} {vehicle.model}' for vehicle in results])
        vehicle = results[0]
        days = state.get('days')
        if not days:
            return response('¿Cuántos días o qué fechas quieres cotizar?', items, source='clarification')
        total = vehicle.daily_price * days
        reply = (f'El precio diario registrado de {vehicle} es ${vehicle.daily_price:,.2f} MXN. '
                 f'Para {days} días, el total estimado es ${total:,.2f} MXN. '
                 f'{date_note} La confirmación se realiza en el formulario de renta; esto no crea una solicitud.')
        result = response(reply, items)
        result['estimate'] = {'days': days, 'daily_price': str(vehicle.daily_price), 'total': str(total)}
        return result
    reply = 'Estas opciones cumplen los filtros indicados. ' + date_note
    if compare:
        lines = [f'{vehicle}: {vehicle.get_category_display()}, {vehicle.passengers} pasajeros, {vehicle.get_transmission_display()}, ${vehicle.daily_price:,.2f} MXN/día.' for vehicle in results]
        reply = 'Comparación de datos registrados:\n' + '\n'.join(lines) + '\n' + date_note
    return response(reply, items, suggestions=['¿Cuál es el más barato?', 'Compara estos vehículos', '¿Qué otros vehículos tienes?'])
