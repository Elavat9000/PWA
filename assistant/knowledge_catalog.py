"""Validar el contenido curado antes de escribir en la base local."""
import json

from django.conf import settings
from django.core.exceptions import ValidationError

from .models import KnowledgeEntry
from .services import question_key


CATALOG_PATH = settings.BASE_DIR / 'assistant' / 'data' / 'knowledge_base.json'


def read_catalog():
    catalog = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    seen_questions = set()
    seen_topics = set()
    if catalog.get('version') != 1 or not catalog.get('topics'):
        raise ValidationError('Versión o contenido de conocimiento inválido.')
    for topic in catalog['topics']:
        if topic['id'] in seen_topics or not topic['category']:
            raise ValidationError('Identificador de tema duplicado o categoría vacía.')
        seen_topics.add(topic['id'])
        if topic['level'] not in {'basico', 'intermedio', 'avanzado'}:
            raise ValidationError('Nivel de conocimiento inválido.')
        if topic['status'] not in KnowledgeEntry.Status.values:
            raise ValidationError('Estado de conocimiento inválido.')
        if not topic['questions'] or not isinstance(topic['answer'], str):
            raise ValidationError('Cada tema necesita preguntas y una respuesta o borrador.')
        if topic['status'] == KnowledgeEntry.Status.PUBLISHED:
            if not topic['answer'].strip() or 'BORRADOR ADMINISTRATIVO' in topic['answer']:
                raise ValidationError('No se puede publicar una respuesta vacía o un borrador.')
        elif not topic.get('review_notes', '').strip():
            raise ValidationError('Una política pendiente necesita indicaciones para su revisión.')
        for source in topic['sources']:
            if source.startswith('local:'):
                local_path = (settings.BASE_DIR / source.removeprefix('local:')).resolve()
                if not local_path.is_relative_to(settings.BASE_DIR) or not local_path.is_file():
                    raise ValidationError('Referencia local inválida.')
            elif source not in catalog['sources']:
                raise ValidationError('Fuente de investigación desconocida.')
        for question in topic['questions']:
            if not isinstance(question, str) or not 2 <= len(question.strip()) <= 400:
                raise ValidationError('Pregunta fuera del límite de 2 a 400 caracteres.')
            key = question_key(question)
            if key in seen_questions:
                raise ValidationError('Hay preguntas equivalentes duplicadas en el catálogo.')
            seen_questions.add(key)
    return catalog
