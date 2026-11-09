"""Carga curada e idempotente; las políticas reales permanecen pendientes."""
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from assistant.knowledge_catalog import read_catalog
from assistant.models import KnowledgeEntry
from assistant.services import question_key


class Command(BaseCommand):
    help = 'Carga conocimiento comprobado y borradores comerciales sin sustituir ediciones.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Muestra cambios sin escribir.')
        parser.add_argument('--complete-pending', action='store_true',
            help='Completa pendientes vacías solo con respuestas públicas comprobadas del catálogo.')

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            catalog = read_catalog()
        except (OSError, ValueError, KeyError, TypeError, ValidationError) as error:
            raise CommandError(f'Catálogo inválido; no se cargó conocimiento: {error}') from error
        existing = {entry.question_key: entry for entry in KnowledgeEntry.objects.all()}
        summary = dict(nuevas_publicadas=0, nuevas_pendientes=0, pendientes_completadas=0,
                       conservadas=0, total_antes=len(existing), simulacion=options['dry_run'])
        for topic in catalog['topics']:
            keys = [question_key(question) for question in topic['questions']]
            status, answer = topic['status'], topic['answer'].strip()
            original = next((existing[key] for key in keys if key in existing), None)
            # Una respuesta humana de referencia también rige las variantes nuevas.
            # Un borrador nunca se convierte en respuesta pública por añadir variantes.
            if status == KnowledgeEntry.Status.PUBLISHED and original is not None:
                can_complete = (options['complete_pending']
                    and original.status == KnowledgeEntry.Status.PENDING and not original.answer.strip())
                if not can_complete:
                    status, answer = original.status, original.answer
            for question, key in zip(topic['questions'], keys):
                entry = existing.get(key)
                if entry is not None:
                    if (options['complete_pending'] and topic['status'] == KnowledgeEntry.Status.PUBLISHED
                            and status == KnowledgeEntry.Status.PUBLISHED
                            and entry.status == KnowledgeEntry.Status.PENDING and not entry.answer.strip()):
                        summary['pendientes_completadas'] += 1
                        if not options['dry_run']:
                            entry.answer = answer
                            entry.status = status
                            entry.save(update_fields=['answer', 'status', 'updated_at'])
                    else:
                        summary['conservadas'] += 1
                    continue
                counter = 'nuevas_publicadas' if status == KnowledgeEntry.Status.PUBLISHED else 'nuevas_pendientes'
                summary[counter] += 1
                if not options['dry_run']:
                    KnowledgeEntry.objects.create(question=question, answer=answer, status=status)
        summary['total_despues'] = summary['total_antes'] + summary['nuevas_publicadas'] + summary['nuevas_pendientes']
        self.stdout.write(json.dumps(summary, ensure_ascii=False))
