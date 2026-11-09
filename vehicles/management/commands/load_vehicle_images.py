from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from vehicles.models import Vehicle
from vehicles.photos import get_reference_photos


class Command(BaseCommand):
    help = 'Asocia las seis fotografías de referencia locales sin sustituir imágenes existentes.'

    def handle(self, *args, **options):
        updated = 0
        for photo in get_reference_photos():
            for vehicle in Vehicle.objects.filter(brand=photo['brand'], model=photo['model'], image=''):
                source = settings.BASE_DIR / 'static/catalog' / photo['filename']
                vehicle.image.save('reference/' + photo['filename'], ContentFile(source.read_bytes()))
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'Imágenes asociadas: {updated}. Las imágenes existentes se conservaron.'))
