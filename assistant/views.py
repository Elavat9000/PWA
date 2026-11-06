import json
import unicodedata

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
    question = data.get('message') if isinstance(data, dict) else None
    if not isinstance(question, str):
        return JsonResponse({'error': 'Escribe una pregunta de entre 2 y 400 caracteres.'}, status=400)
    question = question.strip()
    if (not 2 <= len(question) <= 400 or not any(char.isalnum() for char in question)
            or any(unicodedata.category(char) == 'Cc' and char not in '\n\r\t' for char in question)):
        return JsonResponse({'error': 'Escribe una pregunta de entre 2 y 400 caracteres, sin controles.'}, status=400)
    question = ' '.join(question.split())
    return JsonResponse(answer_question(question, request.user))
