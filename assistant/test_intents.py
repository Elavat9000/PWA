"""Lenguaje cotidiano del usuario y límites de interpretación; SQLite temporal."""
from datetime import date
from decimal import Decimal
from io import StringIO
import json
from unittest.mock import patch

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from rentals.models import RentalRequest
from vehicles.models import Vehicle
from .models import KnowledgeEntry
from .services import answer_question, question_key


class InformalIntentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('load_faq', stdout=StringIO())
        cls.corolla = cls.car('Toyota', 'Corolla', 'sedan', 5, '750.25')
        cls.small_sedan = cls.car('Marca QA', 'Sedan pequeño', 'sedan', 4, '650.00')
        cls.suv = cls.car('Mazda', 'CX-5', 'suv', 7, '1400.00')

    @staticmethod
    def car(brand, model, category, passengers, price):
        return Vehicle.objects.create(brand=brand, model=model, year=2026, category=category,
            passengers=passengers, transmission='automatica', daily_price=Decimal(price), description='QA temporal.')

    def setUp(self):
        clock = patch('django.utils.timezone.localdate', return_value=date(2026, 11, 8))
        clock.start()
        self.addCleanup(clock.stop)

    def ask(self, text, client=None):
        result = (client or self.client).post(reverse('assistant_chat'),
            json.dumps({'message': text}), content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertIn('no-store', result.headers['Cache-Control'])
        return result.json()

    def test_five_original_messages_in_order(self):
        messages = ['Como puedo pedir un carrop', 'como se renta esto ?',
                    'cuantas personas caben en un sedan', 'yo quiero tener un mejor resultado',
                    'crea una renta para el jueves']
        before = KnowledgeEntry.objects.count()
        results = [self.ask(text) for text in messages]
        self.assertEqual([item['source'] for item in results],
                         ['knowledge', 'knowledge', 'vehicles', 'clarification', 'clarification'])
        self.assertIn('Solicitar renta', results[0]['reply'])
        self.assertIn('pasajeros', results[2]['reply'])
        self.assertIn('precio menor', results[3]['reply'])
        self.assertIn('jueves', results[4]['reply'])
        self.assertIn('no crear solicitudes', results[4]['reply'])
        self.assertFalse(RentalRequest.objects.exists())
        self.assertEqual(KnowledgeEntry.objects.count(), before)

    def test_guidance_informal_synonyms_and_typo(self):
        for text in ('Como puedo pedir un carrop', 'cómo se renta esto', 'Como rento un coche',
                     'cómo puedo alquilar un auto', 'como le hago para pedir un carro porfa'):
            with self.subTest(text=text):
                result = self.ask(text)
                self.assertEqual(result['source'], 'knowledge')
                self.assertIn('Pendiente', result['reply'])

    def test_guidance_prefers_admin_reviewed_answer(self):
        entry = KnowledgeEntry.objects.get(question='¿Cómo solicito una renta?')
        entry.answer = 'Instrucciones verificadas y editadas por el administrador de prueba.'
        entry.save()
        self.assertEqual(self.ask('como se renta esto')['reply'], entry.answer)

    def test_guidance_without_published_faq_has_truthful_fallback(self):
        KnowledgeEntry.objects.filter(question='¿Cómo solicito una renta?').delete()
        result = self.ask('como puedo pedir un carro')
        self.assertEqual(result['source'], 'guidance')
        self.assertIn('Solicitar renta', result['reply'])

    def test_pending_admin_draft_is_not_used_as_guidance(self):
        entry = KnowledgeEntry.objects.get(question='¿Cómo solicito una renta?')
        entry.answer = 'Borrador de prueba: no mostrar.'
        entry.status = 'PENDIENTE'
        entry.save()
        self.assertNotIn(entry.answer, self.ask('como se renta esto')['reply'])

    def test_capacity_comes_from_each_actual_record(self):
        result = self.ask('cuantas personas caben en un sedan')
        self.assertEqual({v['id'] for v in result['vehicles']}, {self.corolla.pk, self.small_sedan.pk})
        self.assertIn(f'{self.corolla}: 5 pasajeros.', result['reply'])
        self.assertIn(f'{self.small_sedan}: 4 pasajeros.', result['reply'])
        Vehicle.objects.filter(pk=self.corolla.pk).update(passengers=6)
        result = self.ask('cuantos pasajeros tiene el Corolla')
        self.assertEqual(result['vehicles'][0]['passengers'], 6)
        self.assertIn('6 pasajeros', result['reply'])

    def test_capacity_ignores_stale_static_answer(self):
        KnowledgeEntry.objects.create(question='cuantas personas caben en un sedan', answer='Siempre 99 pasajeros.', status='PUBLICADA')
        self.assertNotIn('99', self.ask('cuantas personas caben en un sedan')['reply'])

    def test_capacity_changes_subject_without_old_suv_filters(self):
        self.ask('Busco camionetas para siete personas')
        result = self.ask('cuantas personas caben en un sedan')
        self.assertEqual({v['id'] for v in result['vehicles']}, {self.corolla.pk, self.small_sedan.pk})

    def test_capacity_reference_uses_selected_vehicle(self):
        self.ask('Precio del Corolla')
        result = self.ask('cuantas personas caben')
        self.assertEqual([v['id'] for v in result['vehicles']], [self.corolla.pk])

    def test_capacity_missing_subject_is_clarified(self):
        result = self.ask('cuantas personas caben')
        self.assertEqual(result['source'], 'clarification')
        self.assertFalse(result['vehicles'])

    def test_unknown_capacity_subject_is_not_invented(self):
        result = self.ask('cuantas personas caben en un Fantasma')
        self.assertEqual(result['source'], 'pending')
        self.assertFalse(result['vehicles'])

    def test_unknown_conditions_not_discarded_by_new_intents(self):
        for text in ('como se renta esto con seguro gratis',
                     'cuantas personas caben en un sedan con seguro',
                     'crea una renta con seguro para el jueves'):
            with self.subTest(text=text):
                result = self.ask(text)
                self.assertEqual(result['source'], 'pending')
                self.assertFalse(result['vehicles'])

    def test_improvement_asks_criterion_and_preserves_filters(self):
        self.ask('Busco camionetas para siete personas')
        result = self.ask('yo quiero tener un mejor resultado')
        self.assertEqual(result['source'], 'clarification')
        result = self.ask('Precio')
        self.assertEqual([v['id'] for v in result['vehicles']], [self.suv.pk])
        self.assertNotIn('clarify', self.client.session['assistant_context']['state'])

    def test_improvement_capacity_followup_and_dates(self):
        self.ask('Busco vehículos')
        self.ask('no me sirven estos resultados')
        self.assertEqual(self.ask('Más espacio')['vehicles'][0]['id'], self.suv.pk)
        self.ask('Del 12 al 15 de noviembre')
        self.ask('quiero mejorar la búsqueda')
        result = self.ask('Otras fechas')
        self.assertEqual(result['source'], 'clarification')
        self.assertNotIn('dates', self.client.session['assistant_context']['state'])
        result = self.ask('Del 16 al 19 de noviembre')
        self.assertTrue(result['vehicles'][0]['availability_checked'])

    def test_improvement_context_is_separate_and_resettable(self):
        self.ask('yo quiero tener un mejor resultado')
        self.assertNotIn('assistant_context', Client().session)
        self.client.post(reverse('assistant_chat'), json.dumps({'action': 'reset'}), content_type='application/json')
        self.assertNotIn('assistant_context', self.client.session)

    def test_each_weekday_requires_explicit_dates(self):
        for weekday in ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'):
            with self.subTest(day=weekday):
                result = self.ask('crea una renta para el ' + weekday)
                self.assertEqual(result['source'], 'clarification')
                self.assertIn('hasta qué fecha', result['reply'])
                self.assertFalse(result['vehicles'])
        self.assertFalse(RentalRequest.objects.exists())

    def test_booking_uses_corrected_dates_but_never_creates_rental(self):
        self.ask('Busco camionetas para siete personas')
        result = self.ask('crea una renta para el jueves')
        self.assertEqual(result['source'], 'clarification')
        result = self.ask('Del 12 al 15 de noviembre')
        self.assertEqual([v['id'] for v in result['vehicles']], [self.suv.pk])
        self.assertTrue(result['vehicles'][0]['availability_checked'])
        self.assertFalse(RentalRequest.objects.exists())

    def test_booking_with_complete_dates_still_only_reads(self):
        result = self.ask('crea una renta del 12 al 15 de noviembre')
        self.assertIn('no crear solicitudes', result['reply'])
        self.assertTrue(result['vehicles'])
        self.assertFalse(RentalRequest.objects.exists())

    def test_booking_without_details_requires_selection(self):
        result = self.ask('crea una renta')
        self.assertEqual(result['source'], 'clarification')
        self.assertIn('Qué vehículo', result['reply'])

    def test_wanting_a_vehicle_is_a_search_not_a_booking(self):
        self.ask('Busco camioneta para siete personas del 12 al 15 de noviembre')
        result = self.ask('Quiero un carro económico')
        self.assertEqual(result['source'], 'vehicles')
        self.assertEqual({vehicle['id'] for vehicle in result['vehicles']},
                         {self.corolla.pk, self.small_sedan.pk, self.suv.pk})
        self.assertNotIn('no crear solicitudes', result['reply'])
        state = self.client.session['assistant_context']['state']
        self.assertNotIn('dates', state)
        self.assertEqual(state['filters'], {})

    def test_topic_change_clears_criterion(self):
        self.ask('yo quiero tener un mejor resultado')
        self.assertEqual(self.ask('¿Puedo pagar aquí?')['source'], 'knowledge')
        self.assertNotIn('assistant_context', self.client.session)

    def test_no_existing_normalized_keys_changed(self):
        before = list(KnowledgeEntry.objects.values_list('pk', 'question_key'))
        for text in ('Como puedo pedir un carrop', 'como se renta esto ?', 'cuantas personas caben en un sedan'):
            self.ask(text)
        self.assertEqual(before, list(KnowledgeEntry.objects.values_list('pk', 'question_key')))
        for entry in KnowledgeEntry.objects.all():
            self.assertEqual(entry.question_key, question_key(entry.question))

    def test_sensitive_input_is_rejected_before_intent_recognition(self):
        result = self.ask('como se renta esto mi correo es privado@example.test')
        self.assertEqual(result['source'], 'privacy')
        self.assertFalse(KnowledgeEntry.objects.filter(question__icontains='privado').exists())

    def test_no_vehicle_data_changed(self):
        before = list(Vehicle.objects.values())
        self.ask('cuantas personas caben en un sedan')
        self.ask('crea una renta para el jueves')
        self.assertEqual(before, list(Vehicle.objects.values()))
