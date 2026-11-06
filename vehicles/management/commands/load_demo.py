from django.core.management.base import BaseCommand
from django.db import transaction
from vehicles.models import Vehicle


DEMO_VEHICLES = [
    ('Nissan', 'March', 2025, 'compacto', 650, 5, 'manual', 'Ágil para la ciudad y fácil de estacionar.'),
    ('Suzuki', 'Swift', 2025, 'compacto', 720, 5, 'automatica', 'Un compañero práctico para tus recorridos diarios.'),
    ('Toyota', 'Corolla', 2026, 'sedan', 950, 5, 'automatica', 'Comodidad para descubrir nuevos destinos en carretera.'),
    ('Volkswagen', 'Jetta', 2025, 'sedan', 1050, 5, 'automatica', 'Espacio y confort para viajes de trabajo o escapadas.'),
    ('Kia', 'Seltos', 2026, 'suv', 1350, 5, 'automatica', 'Versatilidad y espacio para compartir el camino.'),
    ('Mazda', 'CX-5', 2026, 'suv', 1550, 5, 'automatica', 'Una opción amplia y cómoda para viajar en compañía.'),
]


class Command(BaseCommand):
    help = 'Carga seis vehículos ficticios de demostración sin duplicarlos.'

    @transaction.atomic
    def handle(self, *args, **options):
        for brand, model, year, category, price, passengers, transmission, description in DEMO_VEHICLES:
            Vehicle.objects.get_or_create(
                brand=brand, model=model, year=year,
                defaults={
                    'category': category, 'daily_price': price, 'passengers': passengers,
                    'transmission': transmission, 'description': description,
                },
            )
        self.stdout.write(self.style.SUCCESS('Seis vehículos de demostración listos. Los registros existentes se conservaron.'))
