from decimal import Decimal
from io import StringIO
import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from vehicles.models import Vehicle
from .models import KnowledgeEntry
from .services import UNKNOWN_REPLY, answer_question, normalize_text


class AssistantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('load_faq', stdout=StringIO())
        users = get_user_model()
        cls.user = users.objects.create_user('chat_user', password='SoloPrueba!9832')
        cls.admin = users.objects.create_superuser('chat_admin', 'chat@example.test', 'SoloPrueba!9832')
        cls.corolla = cls.vehicle('Toyota', 'Corolla', 'sedan', '750.25', 5, 'automatica')
        cls.seltos = cls.vehicle('Kia', 'Seltos', 'suv', '900.50', 5, 'automatica')
        cls.swift = cls.vehicle('Suzuki', 'Swift', 'compacto', '600.00', 4, 'manual')
        cls.mazda = cls.vehicle('Mazda', 'CX-5', 'suv', '1400.00', 7, 'automatica')
        cls.unavailable = cls.vehicle('Kia', 'Rio', 'sedan', '500.00', 5, 'manual', False)

    @staticmethod
    def vehicle(brand, model, category, price, passengers, transmission, available=True):
        return Vehicle.objects.create(brand=brand, model=model, year=2026, category=category,
                                      daily_price=Decimal(price), passengers=passengers,
                                      transmission=transmission, description='Demo de prueba.', available=available)

    def ask(self, message, client=None):
        return (client or self.client).post(reverse('assistant_chat'),
                                          json.dumps({'message': message}), content_type='application/json')

    def test_normalization_accents_spaces_punctuation_and_synonyms(self):
        self.assertEqual(normalize_text('  ¿COCHES AUTOMÁTICOS?  '), 'vehiculo automatico')
        self.assertEqual(normalize_text('camionta económica'), 'suv barato')

    def test_known_faq_returns_published_answer(self):
        entry = KnowledgeEntry.objects.get(question='¿Cómo puedo registrarme?')
        response = self.ask(entry.question)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reply'], entry.answer)
        self.assertEqual(response.json()['source'], 'knowledge')

    def test_similar_question_and_typo(self):
        for question in ('¿Cómo me registro?', '¿Cómo puedo registarme?'):
            with self.subTest(question=question):
                result = answer_question(question)
                self.assertEqual(result['source'], 'knowledge')
                self.assertIn('Crear cuenta', result['reply'])

    def test_rental_and_vehicle_synonyms(self):
        result = answer_question('¿Cómo puedo alquilar un coche?')
        self.assertEqual(result['source'], 'knowledge')
        self.assertIn('Pendiente', result['reply'])
        for noun in ('autos', 'coches', 'carros', 'automóviles', 'vehículos'):
            with self.subTest(noun=noun):
                self.assertEqual(answer_question(f'¿Qué {noun} tienen disponibles?')['source'], 'vehicles')

    def test_payment_answer_matches_implemented_behavior(self):
        result = answer_question('¿Puedo pagar aquí?')
        self.assertEqual(result['source'], 'knowledge')
        self.assertEqual(result['reply'], 'No. Las solicitudes son simuladas; DriveSmart no procesa pagos.')

    def test_platform_examples_are_known(self):
        for question in ('¿Cómo puedo registrarme?', '¿Cómo solicito una renta?',
                         '¿Dónde consulto mis rentas?', '¿Cómo se calcula el precio?',
                         '¿Cómo se calcula el precio de una renta?', '¿Puedo realizar pagos aquí?'):
            with self.subTest(question=question):
                self.assertEqual(answer_question(question)['source'], 'knowledge')

    def test_inventory_price_takes_priority_over_published_static_price(self):
        KnowledgeEntry.objects.create(question='¿Cuánto cuesta el Toyota Corolla?',
                                      answer='Una tarifa vieja.', status=KnowledgeEntry.Status.PUBLISHED)
        result = answer_question('¿Cuánto cuesta el Toyota Corolla?')
        self.assertEqual(result['source'], 'vehicles')
        self.assertEqual(result['vehicles'][0]['daily_price'], '750.25')

    def test_conflicting_similar_answers_do_not_pick_arbitrarily(self):
        for question, answer in (('¿Mi cobertura especial existe?', 'Primera respuesta.'),
                                 ('¿Su cobertura especial existe?', 'Segunda respuesta.')):
            KnowledgeEntry.objects.create(question=question, answer=answer, status=KnowledgeEntry.Status.PUBLISHED)
        self.assertEqual(answer_question('¿La cobertura especial existe?')['source'], 'pending')

    def test_inventory_only_real_available_records_and_limit_three(self):
        result = answer_question('¿Qué autos tienen disponibles?')
        self.assertEqual(result['source'], 'vehicles')
        self.assertEqual(len(result['vehicles']), 3)
        for item in result['vehicles']:
            vehicle = Vehicle.objects.get(pk=item['id'])
            self.assertTrue(vehicle.available)
            self.assertEqual(item['daily_price'], str(vehicle.daily_price))
            self.assertEqual(item['name'], str(vehicle))
            self.assertEqual(item['url'], reverse('vehicle_detail', args=[vehicle.pk]))

    def test_cheapest_order_and_synonym(self):
        for question in ('¿Cuáles son los autos más baratos?', 'Busco coches económicos'):
            self.assertEqual([v['id'] for v in answer_question(question)['vehicles']],
                             [self.swift.pk, self.corolla.pk, self.seltos.pk])

    def test_typo_category_and_passengers(self):
        result = answer_question('Busco una camionta para 5 personas')
        self.assertEqual({v['id'] for v in result['vehicles']}, {self.seltos.pk, self.mazda.pk})

    def test_transmission_and_minimum_passengers(self):
        result = answer_question('Busco autos automáticos para 7 personas')
        self.assertEqual([v['id'] for v in result['vehicles']], [self.mazda.pk])
        result = answer_question('¿Tienen vehículos manuales para 5 personas?')
        self.assertEqual(result['vehicles'], [])

    def test_brand_model_price_matches_database_and_updates(self):
        result = answer_question('¿Cuánto cuesta el Toyota Corolla?')
        self.assertEqual([v['id'] for v in result['vehicles']], [self.corolla.pk])
        self.assertEqual(result['vehicles'][0]['daily_price'], '750.25')
        Vehicle.objects.filter(pk=self.corolla.pk).update(daily_price=Decimal('812.30'))
        self.assertEqual(answer_question('Precio del Corolla')['vehicles'][0]['daily_price'], '812.30')

    def test_price_of_unavailable_vehicle_does_not_invent_availability(self):
        result = answer_question('Precio del Kia Rio')
        self.assertEqual(result['vehicles'][0]['id'], self.unavailable.pk)
        self.assertFalse(result['vehicles'][0]['available'])

    def test_price_budget_respects_decimal_and_boundaries(self):
        result = answer_question('Busco autos hasta 750.25 pesos')
        self.assertEqual([v['id'] for v in result['vehicles']], [self.swift.pk, self.corolla.pk])
        result = answer_question('Busco autos menos de 750.25 pesos')
        self.assertEqual([v['id'] for v in result['vehicles']], [self.swift.pk])
        result = answer_question('Busco autos desde 700 hasta 1000 pesos')
        self.assertEqual([v['id'] for v in result['vehicles']], [self.corolla.pk, self.seltos.pk])

    def test_no_matching_vehicle_does_not_fabricate_results(self):
        result = answer_question('Busco autos para 20 personas')
        self.assertEqual(result['source'], 'vehicles')
        self.assertEqual(result['vehicles'], [])
        result = answer_question('¿Cuánto cuesta el vehículo Fantasma?')
        self.assertEqual(result['vehicles'], [])
        self.assertEqual(result['source'], 'pending')

    def test_unknown_vehicle_conditions_not_silently_ignored(self):
        for question in ('¿Tienen camionetas con seguro?', 'Busco autos eléctricos',
                         'Busco autos no automáticos', 'Busco autos para 5 personas para 7 personas'):
            with self.subTest(question=question):
                self.assertEqual(answer_question(question)['source'], 'pending')

    def test_unknown_question_saved_pending_with_optional_user(self):
        question = '¿Los vehículos incluyen seguro de cobertura amplia?'
        result = answer_question(question, self.user)
        self.assertEqual(result['reply'], UNKNOWN_REPLY)
        entry = KnowledgeEntry.objects.get(question=question)
        self.assertEqual(entry.status, KnowledgeEntry.Status.PENDING)
        self.assertEqual(entry.answer, '')
        self.assertEqual(entry.asked_by, self.user)

    def test_equivalent_pending_question_deduplicated(self):
        answer_question('¿Los vehículos incluyen seguro de cobertura amplia?')
        answer_question('¿Los coches incluyen seguro de cobertura amplia?')
        answer_question('¿Incluyen seguro de cobertura amplia los autos?')
        self.assertEqual(KnowledgeEntry.objects.filter(status=KnowledgeEntry.Status.PENDING).count(), 1)

    def test_draft_answer_never_used_until_published(self):
        entry = KnowledgeEntry.objects.create(question='¿Tienen seguro de cobertura amplia?', answer='Respuesta aún sin revisar.')
        result = answer_question(entry.question)
        self.assertEqual(result['source'], 'pending')
        self.assertNotIn(entry.answer, result['reply'])

    def test_admin_publishes_then_similar_question_reuses_answer(self):
        question = '¿Los vehículos incluyen seguro de cobertura amplia?'
        answer_question(question, self.user)
        entry = KnowledgeEntry.objects.get(status=KnowledgeEntry.Status.PENDING)
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin:assistant_knowledgeentry_change', args=[entry.pk]), {
            'question': entry.question, 'answer': 'Respuesta revisada por el administrador de prueba.',
            'status': KnowledgeEntry.Status.PUBLISHED, '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.status, KnowledgeEntry.Status.PUBLISHED)
        result = answer_question('¿Incluyen seguro de cobertura amplia los coches?')
        self.assertEqual(result['reply'], entry.answer)
        self.assertEqual(result['source'], 'knowledge')

    def test_empty_publication_blocked_in_model_and_admin(self):
        entry = KnowledgeEntry.objects.create(question='¿Hay seguro?')
        entry.status = KnowledgeEntry.Status.PUBLISHED
        entry.answer = '   '
        with self.assertRaises(ValidationError):
            entry.save()
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin:assistant_knowledgeentry_change', args=[entry.pk]), {
            'question': entry.question, 'answer': '', 'status': KnowledgeEntry.Status.PUBLISHED, '_save': 'Guardar',
        })
        self.assertContains(response, 'Escribe una respuesta antes de publicar.')
        entry.refresh_from_db()
        self.assertEqual(entry.status, KnowledgeEntry.Status.PENDING)

    def test_shared_words_and_different_qualifiers_do_not_match(self):
        KnowledgeEntry.objects.create(question='¿Incluyen seguro de cobertura amplia?',
                                      answer='Respuesta específica y revisada.', status=KnowledgeEntry.Status.PUBLISHED)
        for question in ('¿Incluyen seguro de cobertura limitada?', '¿No incluyen seguro de cobertura amplia?',
                         '¿Dónde consulto el precio de mi renta?'):
            with self.subTest(question=question):
                self.assertEqual(answer_question(question)['source'], 'pending')

    def test_normal_user_cannot_publish_or_inject_knowledge(self):
        entry = KnowledgeEntry.objects.create(question='¿Existe una condición nueva?')
        self.client.force_login(self.user)
        response = self.client.post(reverse('admin:assistant_knowledgeentry_change', args=[entry.pk]), {
            'question': entry.question, 'answer': 'No autorizada', 'status': KnowledgeEntry.Status.PUBLISHED,
        })
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse('assistant_chat'), json.dumps({
            'message': entry.question, 'answer': 'No autorizada', 'status': KnowledgeEntry.Status.PUBLISHED,
        }), content_type='application/json')
        self.assertEqual(response.json()['source'], 'pending')
        entry.refresh_from_db()
        self.assertEqual(entry.status, KnowledgeEntry.Status.PENDING)
        self.assertEqual(entry.answer, '')

    def test_staff_without_permission_cannot_publish(self):
        self.user.is_staff = True
        self.user.save()
        entry = KnowledgeEntry.objects.create(question='¿Hay otra política?')
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('admin:assistant_knowledgeentry_change', args=[entry.pk])).status_code, 403)

    def test_endpoint_rejects_bad_content(self):
        for data in ({}, [], {'message': None}, {'message': 4}, {'message': ''},
                     {'message': 'x'}, {'message': 'x' * 401}, {'message': '?!'}, {'message': 'hola\x00'}):
            with self.subTest(data=data):
                response = self.client.post(reverse('assistant_chat'), json.dumps(data), content_type='application/json')
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post(reverse('assistant_chat'), '{', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post(reverse('assistant_chat'), 'x' * 5000, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post(reverse('assistant_chat'), {'message': 'hola'}).status_code, 415)

    def test_endpoint_rejects_wrong_methods(self):
        self.assertEqual(self.client.get(reverse('assistant_chat')).status_code, 405)
        self.assertEqual(self.client.put(reverse('assistant_chat'), '{}', content_type='application/json').status_code, 405)

    def test_input_whitespace_is_normalized(self):
        result = self.ask('  ¿Cómo\n puedo\t registrarme?  ')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['source'], 'knowledge')

    def test_csrf_required_and_foreign_origin_rejected(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.ask('¿Cómo puedo registrarme?', client).status_code, 403)
        client.get(reverse('home'))
        token = client.cookies['csrftoken'].value
        args = {'content_type': 'application/json', 'HTTP_X_CSRFTOKEN': token}
        self.assertEqual(client.post(reverse('assistant_chat'), json.dumps({'message': '¿Cómo puedo registrarme?'}), **args).status_code, 200)
        self.assertEqual(client.post(reverse('assistant_chat'), json.dumps({'message': 'Hola'}),
                                    HTTP_ORIGIN='https://sitio-ajeno.example', **args).status_code, 403)

    def test_demo_repeatable_and_preserves_admin_edits(self):
        entry = KnowledgeEntry.objects.get(question='¿Cómo puedo registrarme?')
        entry.question = '¿Cómo me registro?'
        entry.answer = 'Edición autorizada para prueba.'
        entry.save()
        call_command('load_faq', stdout=StringIO())
        call_command('load_faq', stdout=StringIO())
        self.assertEqual(KnowledgeEntry.objects.count(), 8)
        entry.refresh_from_db()
        self.assertEqual(entry.answer, 'Edición autorizada para prueba.')

    def test_normalized_duplicate_entry_blocked(self):
        KnowledgeEntry.objects.create(question='¿Hay cobertura especial?')
        with self.assertRaises(ValidationError):
            KnowledgeEntry.objects.create(question='HAY COBERTURA ESPECIAL!')

    def test_questions_do_not_change_rentals_or_vehicle_records(self):
        from rentals.models import RentalRequest
        vehicles = list(Vehicle.objects.values())
        answer_question('¿Tienen camionetas?')
        answer_question('¿Hay cobertura amplia?')
        self.assertEqual(list(Vehicle.objects.values()), vehicles)
        self.assertFalse(RentalRequest.objects.exists())
