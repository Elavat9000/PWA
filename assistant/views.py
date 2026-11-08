import json
import unicodedata
import time

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services import answer_question


@require_POST
def chat(request):
    if request.content_type != 'application/json':
        return JsonResponse({'error': 'Envía la pregunta como JSON.'}, status=415)
    if len(request.body) > 4096:
        return JsonResponse({'error': 'El mensaje es demasiado largo.'}, status=400)
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'La solicitud no contiene JSON válido.'}, status=400)
    if isinstance(data, dict) and data.get('action') == 'reset':
        request.session.pop('assistant_context', None)
        return JsonResponse({'reply': 'Nueva conversación. ¿Qué vehículo necesitas?',
                             'vehicles': [], 'source': 'reset', 'suggestions': []})
    question = data.get('message') if isinstance(data, dict) else None
    if not isinstance(question, str):
        return JsonResponse({'error': 'Escribe una pregunta de entre 2 y 400 caracteres.'}, status=400)
    question = question.strip()
    if (not 2 <= len(question) <= 400 or not any(char.isalnum() for char in question)
            or any(unicodedata.category(char) == 'Cc' and char not in '\n\r\t' for char in question)):
        return JsonResponse({'error': 'Escribe una pregunta de entre 2 y 400 caracteres, sin controles.'}, status=400)
    question = ' '.join(question.split())
    owner = str(request.user.pk) if request.user.is_authenticated else 'anonymous'
    saved = request.session.get('assistant_context', {})
    if not isinstance(saved, dict) or saved.get('owner') != owner or time.time() - saved.get('updated', 0) > 1800:
        saved = {}
    context = saved.get('state', {})
    if not isinstance(context, dict):
        context = {}
    result = answer_question(question, request.user, context=context)
    if context:
        request.session['assistant_context'] = {'owner': owner, 'updated': time.time(), 'state': context}
    elif 'assistant_context' in request.session:
        del request.session['assistant_context']
    return JsonResponse(result)
