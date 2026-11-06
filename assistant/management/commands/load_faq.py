from django.core.management.base import BaseCommand
from django.db import transaction

from assistant.models import KnowledgeEntry
from assistant.services import matching_entry, question_key


FAQ = [
    ('¿Cómo puedo registrarme?',
     'Usa Crear cuenta y completa el nombre de usuario y las dos contraseñas. Al terminar el registro se inicia tu sesión.'),
    ('¿Cómo solicito una renta?',
     'Abre el catálogo y el detalle de un vehículo disponible. Pulsa Solicitar renta, inicia sesión, elige las fechas, '
     'calcula el costo y confirma. La solicitud queda Pendiente hasta la revisión del administrador.'),
    ('¿Dónde consulto mis rentas?',
     'Inicia sesión y abre Mis rentas (/mis-rentas/). Allí solo aparecen tus propias solicitudes y sus estados.'),
    ('¿Cómo se calcula el precio?',
     'El precio diario vigente al confirmar se multiplica por los días entre inicio y devolución. '
     'Del 10 al 13 de noviembre son tres días. Ese precio y total se guardan en la solicitud.'),
    ('¿Puedo realizar pagos aquí?',
     'No. Las solicitudes son simuladas; DriveSmart no procesa pagos.'),
    ('¿Quién aprueba mi solicitud de renta?',
     'El administrador autorizado revisa las solicitudes en Django Admin y puede aprobarlas o rechazarlas. '
     'Antes de aprobar se comprueba que no coincidan con otra renta aprobada del mismo vehículo.'),
    ('¿Puedo cancelar o editar mi solicitud?',
     'En esta fase no puedes editar ni cancelar solicitudes desde tu cuenta. Puedes consultar su estado en Mis rentas.'),
    ('¿Cómo sé si un vehículo está disponible?',
     'El catálogo indica Disponible o No disponible. Al solicitar y al aprobar se comprueban también las fechas. '
     'Las solicitudes pendientes pueden coincidir; una aprobada reserva ese intervalo.'),
]


class Command(BaseCommand):
    help = 'Carga ocho preguntas frecuentes verdaderas sin sobrescribir entradas existentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for question, answer in FAQ:
            if matching_entry(question, KnowledgeEntry.objects.all()):
                continue
            _, is_new = KnowledgeEntry.objects.get_or_create(
                question_key=question_key(question), defaults={
                    'question': question, 'answer': answer, 'status': KnowledgeEntry.Status.PUBLISHED,
                },
            )
            created += is_new
        self.stdout.write(self.style.SUCCESS(f'FAQ listas: {created} creadas; las entradas existentes se conservaron.'))
