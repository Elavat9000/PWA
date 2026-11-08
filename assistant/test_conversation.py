"""Regresión de Chat 2.0, siempre en la base temporal del runner Django."""
from datetime import date
from decimal import Decimal
from io import StringIO
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from rentals.models import RentalRequest
from vehicles.models import Vehicle
from .models import KnowledgeEntry
from .services import answer_question


class ConversationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('load_faq', stdout=StringIO())
        cls.user = get_user_model().objects.create_user('chat2_test')
        cls.corolla = cls.car('Toyota', 'Corolla', 'sedan', '750.25', 5)
        cls.seltos = cls.car('Kia', 'Seltos', 'suv', '900.50', 5)
        cls.mazda = cls.car('Mazda', 'CX-5', 'suv', '1400.00', 7)
        cls.swift = cls.car('Suzuki', 'Swift', 'compacto', '600.00', 4, 'manual')
        cls.rio = cls.car('Kia', 'Rio', 'sedan', '500.00', 5, available=False)

    @staticmethod
    def car(brand, model, category, price, passengers, transmission='automatica', available=True):
        return Vehicle.objects.create(brand=brand, model=model, year=2026, category=category,
            daily_price=Decimal(price), passengers=passengers, transmission=transmission,
            available=available, description='Datos temporales de QA.')

    def setUp(self):
        self.clock = patch('django.utils.timezone.localdate', return_value=date(2026, 11, 8))
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def ask(self, text, client=None):
        response = (client or self.client).post(reverse('assistant_chat'),
            json.dumps({'message': text}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        return response.json()

    def reset(self):
        return self.client.post(reverse('assistant_chat'), json.dumps({'action': 'reset'}), content_type='application/json')

    def ids(self, result):
        return [item['id'] for item in result['vehicles']]

    def reserve(self, vehicle, start, end, status='APROBADA'):
        return RentalRequest.objects.create(user=self.user, vehicle=vehicle,
            start_date=date.fromisoformat(start), end_date=date.fromisoformat(end), status=status)

    def test_combined_words_typo_and_seven_passengers(self):
        for text in ('Necesito una camioneta automática para siete personas',
                     'Busco una camionta automatica para 7 pasajeros'):
            with self.subTest(text=text):
                self.assertEqual(self.ids(self.ask(text)), [self.mazda.pk])

    def test_memory_dates_then_cheapest_and_estimate(self):
        self.assertEqual(self.ids(self.ask('Busco una camioneta automática para cinco personas')), [self.seltos.pk, self.mazda.pk])
        self.ask('Del 12 al 15 de noviembre')
        result = self.ask('¿Y el más barato?')
        self.assertEqual(self.ids(result), [self.seltos.pk])
        self.assertTrue(result['vehicles'][0]['availability_checked'])
        result = self.ask('¿Cuánto cuesta rentarlo tres días?')
        self.assertEqual(result['estimate'], {'days': 3, 'daily_price': '900.50', 'total': '2701.50'})
        self.assertIn('estimado', result['reply'])

    def test_new_search_replaces_all_filters(self):
        self.ask('Busco camioneta automática para siete personas hasta 1500 pesos')
        self.ask('Del 12 al 15 de noviembre')
        result = self.ask('Quiero un carro económico')
        self.assertEqual(self.ids(result), [self.swift.pk, self.corolla.pk, self.seltos.pk])
        state = self.client.session['assistant_context']['state']
        self.assertNotIn('dates', state)
        self.assertEqual(state['filters'], {})

    def test_model_change_does_not_keep_suv_filter(self):
        self.ask('Busco una camioneta para siete personas')
        self.assertEqual(self.ids(self.ask('Precio del Corolla')), [self.corolla.pk])

    def test_reset_clears_only_assistant_state(self):
        session = self.client.session
        session['unrelated'] = 'conservar'
        session.save()
        self.ask('Busco camionetas')
        self.assertEqual(self.reset().json()['source'], 'reset')
        self.assertNotIn('assistant_context', self.client.session)
        self.assertEqual(self.client.session['unrelated'], 'conservar')

    def test_sessions_are_separate(self):
        self.ask('Busco camionetas')
        other = Client()
        result = self.ask('¿Cuál es el más barato?', other)
        self.assertEqual(self.ids(result), [self.swift.pk])
        self.assertEqual(self.client.session['assistant_context']['state']['filters']['category'], 'suv')

    def test_topic_change_does_not_contaminate(self):
        self.ask('Busco camionetas para siete personas')
        self.assertEqual(self.ask('¿Puedo pagar aquí?')['source'], 'knowledge')
        self.assertNotIn('assistant_context', self.client.session)
        self.assertEqual(self.ids(self.ask('¿Cuál es el más barato?')), [self.swift.pk])

    def test_explicit_date_formats(self):
        for text in ('Autos del 12/11/2026 al 15/11/2026', 'Autos del 2026-11-12 al 2026-11-15',
                     'Autos del 12 de noviembre al 15 de noviembre de 2026'):
            with self.subTest(text=text):
                result = self.ask(text)
                self.assertTrue(result['vehicles'], result)
                self.assertTrue(all(item['availability_checked'] for item in result['vehicles']))

    def test_invalid_past_and_ambiguous_dates(self):
        for text in ('Autos del 31 al 32 de noviembre', 'Autos del 1 al 3 de noviembre',
                     'Autos del 15 al 12 de noviembre', 'Autos del 12 al 15',
                     'Autos del 12/11/2026', 'Autos para mañana'):
            with self.subTest(text=text):
                result = self.ask(text)
                self.assertEqual(result['source'], 'clarification', result)
                self.assertFalse(result['vehicles'])

    def test_approved_overlap_is_excluded(self):
        self.reserve(self.seltos, '2026-11-12', '2026-11-15')
        result = self.ask('Camionetas del 13 al 16 de noviembre')
        self.assertEqual(self.ids(result), [self.mazda.pk])

    def test_pending_does_not_block(self):
        self.reserve(self.seltos, '2026-11-12', '2026-11-15', 'PENDIENTE')
        self.assertIn(self.seltos.pk, self.ids(self.ask('Camionetas del 13 al 16 de noviembre')))

    def test_adjacent_intervals_do_not_overlap(self):
        self.reserve(self.seltos, '2026-11-12', '2026-11-15')
        for text in ('Camionetas del 15 al 18 de noviembre', 'Camionetas del 10 al 12 de noviembre'):
            self.assertIn(self.seltos.pk, self.ids(self.ask(text)))

    def test_database_changes_are_rechecked_on_followup(self):
        self.ask('Camionetas del 12 al 15 de noviembre')
        self.reserve(self.seltos, '2026-11-12', '2026-11-15')
        self.assertEqual(self.ids(self.ask('¿Y el más barato?')), [self.mazda.pk])

    def test_no_results_keeps_all_constraints(self):
        result = self.ask('Camioneta automática para veinte personas hasta 1000 pesos')
        self.assertEqual(self.ids(result), [])
        self.assertEqual(self.ids(self.ask('¿Y el más barato?')), [])
        self.assertEqual(self.client.session['assistant_context']['state']['filters']['passengers'], 20)

    def test_comparison_real_fields_only(self):
        result = self.ask('Compara los SUV disponibles')
        self.assertEqual(self.ids(result), [self.seltos.pk, self.mazda.pk])
        for vehicle in (self.seltos, self.mazda):
            self.assertIn(str(vehicle), result['reply'])
            self.assertIn(str(vehicle.daily_price), result['vehicles'][self.ids(result).index(vehicle.pk)]['daily_price'])
        self.assertNotIn('consumo', result['reply'])

    def test_compare_named_models_and_followup_subset(self):
        self.assertEqual(self.ids(self.ask('Compara Corolla y Seltos')), [self.corolla.pk, self.seltos.pk])
        result = self.ask('¿Qué diferencia hay entre estos dos vehículos?')
        self.assertEqual(self.ids(result), [self.corolla.pk, self.seltos.pk])

    def test_more_capacity_and_other_options(self):
        self.ask('Precio del Corolla')
        self.assertEqual(self.ids(self.ask('¿Y uno más grande?')), [self.mazda.pk])
        self.reset()
        first = self.ids(self.ask('¿Qué autos tienes?'))
        second = self.ids(self.ask('¿Qué otros vehículos tienes?'))
        self.assertTrue(second)
        self.assertFalse(set(first) & set(second))

    def test_something_cheaper_keeps_category(self):
        self.ask('Busco camionetas')
        result = self.ask('¿Tienen algo más barato?')
        self.assertEqual(self.ids(result), [])

    def test_best_requires_criterion(self):
        self.ask('Busco camionetas')
        result = self.ask('¿Cuál conviene más?')
        self.assertEqual(result['source'], 'clarification')
        self.assertEqual(self.ids(self.ask('¿Cuál tiene más capacidad?')), [self.mazda.pk])

    def test_estimate_decimal_and_no_rental_write(self):
        before = list(Vehicle.objects.values())
        result = self.ask('¿Cuánto cuesta rentar el Corolla tres días?')
        self.assertEqual(Decimal(result['estimate']['total']), Decimal('2250.75'))
        self.assertFalse(result['vehicles'][0]['availability_checked'])
        self.assertFalse(RentalRequest.objects.exists())
        self.assertEqual(before, list(Vehicle.objects.values()))

    def test_estimate_ambiguous_then_model_selection(self):
        result = self.ask('¿Cuánto cuesta rentar autos tres días?')
        self.assertNotIn('estimate', result)
        self.assertIn('modelo', result['reply'])
        result = self.ask('Precio del Corolla')
        self.assertEqual(result['estimate']['total'], '2250.75')

    def test_mismatched_days_and_dates_are_not_quoted(self):
        result = self.ask('Precio del Corolla tres días del 12 al 16 de noviembre')
        self.assertEqual(result['source'], 'clarification')
        self.assertNotIn('estimate', result)

    def test_unavailable_price_keeps_flag(self):
        context = {}
        result = answer_question('Precio del Kia Rio', context=context)
        self.assertEqual(self.ids(result), [self.rio.pk], (result, context))
        self.assertFalse(result['vehicles'][0]['available'])

    def test_unknown_conditions_pending_and_draft_not_promoted(self):
        self.ask('Busco camionetas')
        result = self.ask('¿Tienen camionetas con seguro?')
        self.assertEqual(result['source'], 'pending')
        entry = KnowledgeEntry.objects.get(question='¿Tienen camionetas con seguro?')
        entry.answer = 'Borrador secreto de QA.'
        entry.save()
        self.assertNotIn(entry.answer, self.ask(entry.question)['reply'])
        entry.status = 'PUBLICADA'
        entry.answer = 'Respuesta revisada en esta prueba.'
        entry.save()
        self.assertEqual(self.ask(entry.question)['reply'], entry.answer)

    def test_unknown_vehicle_and_duplicate_questions(self):
        self.assertEqual(self.ask('Precio del coche Fantasma')['source'], 'pending')
        self.ask('¿Los coches incluyen seguro de cobertura amplia?')
        self.ask('¿Incluyen seguro de cobertura amplia los autos?')
        self.assertEqual(KnowledgeEntry.objects.filter(question__icontains='cobertura').count(), 1)

    def test_no_sensitive_input_in_context(self):
        self.ask('Busco camionetas')
        self.ask('Mi contraseña es secreta123')
        self.assertNotIn('secreta123', json.dumps(dict(self.client.session)))
        self.assertFalse(KnowledgeEntry.objects.filter(question__icontains='secreta123').exists())

    def test_login_does_not_inherit_anonymous_context(self):
        self.ask('Busco camionetas')
        self.client.force_login(self.user)
        self.assertEqual(self.ids(self.ask('¿Cuál es el más barato?')), [self.swift.pk])

    def test_expired_context_is_cleared(self):
        self.ask('Busco camionetas')
        session = self.client.session
        saved = session['assistant_context']
        saved['updated'] = 0
        session['assistant_context'] = saved
        session.save()
        self.assertEqual(self.ids(self.ask('¿Cuál es el más barato?')), [self.swift.pk])

    def test_csrf_reset_protected_and_no_store(self):
        client = Client(enforce_csrf_checks=True)
        url = reverse('assistant_chat')
        payload = json.dumps({'action': 'reset'})
        self.assertEqual(client.post(url, payload, content_type='application/json').status_code, 403)
        client.get('/')
        result = client.post(url, payload, content_type='application/json', HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value)
        self.assertEqual(result.status_code, 200)
        self.assertIn('no-store', result.headers['Cache-Control'])

    def test_pwa_only_cache_version_changed(self):
        from django.conf import settings
        source = (settings.BASE_DIR / 'static/pwa/service-worker.js').read_text(encoding='utf-8')
        self.assertIn('v9', source)
        self.assertNotIn('/asistente/consultar/', source.split('];', 1)[0])
        js = (settings.BASE_DIR / 'static/js/assistant.js').read_text(encoding='utf-8')
        self.assertNotIn('innerHTML', js)
        self.assertIn('textContent', js)
        self.assertIn('Nueva conversación', self.client.get('/').content.decode())

    def test_followup_capacity_and_budget(self):
        self.ask('Busco camionetas')
        self.assertEqual(self.ids(self.ask('Para siete personas')), [self.mazda.pk])
        self.assertEqual(self.ids(self.ask('Hasta 1000 pesos')), [])

    def test_extreme_capacity_never_ignored(self):
        result = self.ask('Camioneta para 100 personas')
        self.assertEqual(result['source'], 'clarification')
        self.assertFalse(result['vehicles'])

    def test_reference_without_context_is_clarified(self):
        for text in ('¿Cuánto cuesta rentarlo?', '¿Y uno más grande?', 'Compara estos dos'):
            with self.subTest(text=text):
                self.assertEqual(self.ask(text)['source'], 'clarification')

    def test_unknown_features_with_dates_not_discarded(self):
        for text in ('Camionetas con seguro del 12 al 15 de noviembre',
                     'Camionetas con seguro del 31 al 32 de noviembre'):
            with self.subTest(text=text):
                result = self.ask(text)
                self.assertEqual(result['source'], 'pending')
                self.assertFalse(result['vehicles'])

    def test_invalid_followup_does_not_keep_old_dates(self):
        self.ask('Camionetas del 12 al 15 de noviembre')
        self.assertEqual(self.ask('Del 31 al 32 de noviembre')['source'], 'clarification')
        result = self.ask('¿Y el más barato?')
        self.assertFalse(result['vehicles'][0]['availability_checked'])

    def test_duration_limit_and_bad_budget(self):
        for text in ('Precio del Corolla cero días', 'Precio del Corolla 4000 días', 'Autos hasta 0 pesos'):
            with self.subTest(text=text):
                result = self.ask(text)
                self.assertNotIn('estimate', result)
                self.assertFalse(result['vehicles'])
