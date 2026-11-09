"""Intenciones informales acotadas; reutiliza las consultas y protecciones del chat."""
import re

from .conversation import DATE_HELP, contextual_reply, response
from .models import KnowledgeEntry


GUIDE = ('Abre el catálogo y el detalle de un vehículo disponible. Pulsa Solicitar renta, '
         'inicia sesión, elige las fechas, calcula el costo y confirma. '
         'La solicitud queda Pendiente hasta la revisión del administrador.')
BOOKING_LIMIT = ('Puedo ayudarte a buscar, pero no crear solicitudes desde el chat. '
                 'La confirmación se realiza en el formulario de renta. ')


def informal_reply(question, context):
    from .services import matching_entry, normalize_text

    text = normalize_text(question)
    # Correcciones locales: no alteran las huellas de KnowledgeEntry ya existentes.
    text = re.sub(r'\b(?:por favor|porfa)\b', '', text)
    text = ' '.join(text.split())
    guide = re.fullmatch(
        r'(?:hola )?como (?:puedo |podria |se |hago para |le hago para )?'
        r'(?:pedir|solicitar(?: renta)?|rento|renta|reservar|reservo)'
        r'(?: (?:un|una|el|la|este|esto|vehiculo|aqui|en|drivesmart|lo|hago))*', text)
    if guide:
        context.clear()
        published = KnowledgeEntry.objects.filter(status=KnowledgeEntry.Status.PUBLISHED).exclude(answer='')
        entry = matching_entry('¿Cómo solicito una renta?', published)
        return response(entry.answer if entry else GUIDE, source='knowledge' if entry else 'guidance',
                        suggestions=['¿Qué vehículos tienen disponibles?'])

    dissatisfaction = re.fullmatch(
        r'(?:(?:yo )?quiero (?:tener un mejor resultado|mejorar (?:la busqueda|los resultados))'
        r'|no (?:me sirven estos resultados|es lo que busco|me gusta ninguna opcion)'
        r'|busco algo mejor)', text)
    if dissatisfaction:
        context['clarify'] = 'criterion'
        return response('¿Qué quieres mejorar: encontrar un precio menor, más espacio o disponibilidad para otras fechas?',
                        source='clarification', suggestions=['Precio', 'Más espacio', 'Otras fechas'])

    if context.get('clarify') == 'criterion':
        criteria = {'precio': '¿Cuál es el más barato?', 'mas barato': '¿Cuál es el más barato?',
                    'presupuesto': '¿Cuál es el más barato?', 'mas espacio': '¿Cuál tiene más capacidad?',
                    'espacio': '¿Cuál tiene más capacidad?', 'capacidad': '¿Cuál tiene más capacidad?'}
        if text in criteria:
            context.pop('clarify', None)
            return contextual_reply(criteria[text], context)
        if text in {'otras fechas', 'fechas', 'cambiar fechas'}:
            context.pop('clarify', None)
            for key in ('dates', 'days', 'result_ids', 'selected_id', 'awaiting_vehicle'):
                context.pop(key, None)
            return response('¿Qué fechas de inicio y devolución necesitas? ' + DATE_HELP, source='clarification')
        context.pop('clarify', None)

    capacity = re.match(r'^(?:cuantas personas|cuantos pasajeros|cuantas plazas|que capacidad)\b(.*)$', text)
    if capacity:
        target = re.sub(r'\b(?:caben|entran|tiene|tienen|hay|lleva|llevan|es|en|de|un|una|el|la|los|las|este|ese|estos|esos)\b', ' ', capacity[1])
        target = ' '.join(target.split())
        if not target and not context.get('filters') and not context.get('selected_id'):
            return response('¿De qué modelo o categoría quieres conocer la capacidad?', source='clarification')
        query = 'busco ' + target if target else 'vehiculo rentarlo'
        result = contextual_reply(query, context)
        if result and result['source'] == 'vehicles' and result['vehicles']:
            lines = [f"{vehicle['name']}: {vehicle['passengers']} pasajeros." for vehicle in result['vehicles']]
            result['reply'] = ('Capacidad registrada de hasta tres modelos que coinciden con tu consulta:\n'
                               + '\n'.join(lines) + '\n' + result['reply'])
        return result

    booking = re.fullmatch(
        r'(?:crea(?:r)?|haz|genera(?:r)?|reserva(?:r)?|(?:yo )?quiero (?:crear|hacer|reservar|solicitar))'
        r' (?:una? |la |el )?(?:renta|reserva|vehiculo)\b(.*)', text)
    if not booking:
        booking = re.fullmatch(
            r'(?:yo )?quiero (?:una? |la |el )?(?:renta|reserva)\b(.*)', text)
    if booking:
        target = booking[1].strip()
        if not target and not context:
            return response(BOOKING_LIMIT + '¿Qué vehículo necesitas y para qué fechas?', source='clarification')
        result = contextual_reply('vehiculo ' + target, context)
        if result:
            result['reply'] = BOOKING_LIMIT + result['reply']
        return result
    return None
