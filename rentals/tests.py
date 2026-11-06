from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from vehicles.models import Vehicle
from .models import RentalRequest


class RentalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.user = users.objects.create_user('renter', password='Ruta!3872x')
        cls.other = users.objects.create_user('other', password='Ruta!3872x')
        cls.admin = users.objects.create_superuser('rental_admin', 'rental@example.test', 'Ruta!3872x')
        cls.vehicle = Vehicle.objects.create(
            brand='Demo', model='Ruta', year=2026, category='sedan',
            daily_price=Decimal('750.25'), passengers=5, transmission='automatica',
            description='Vehículo de prueba.',
        )

    def setUp(self):
        self.start = timezone.localdate() + timedelta(days=10)
        self.end = self.start + timedelta(days=3)
        self.url = reverse('rental_create', args=[self.vehicle.pk])
        self.client.force_login(self.user)

    def dates(self, **extra):
        return {'start_date': self.start.isoformat(), 'end_date': self.end.isoformat(), **extra}

    def make_request(self, **overrides):
        data = {'user': self.user, 'vehicle': self.vehicle,
                'start_date': self.start, 'end_date': self.end}
        return RentalRequest.objects.create(**(data | overrides))

    def test_anonymous_redirect_and_login_return(self):
        self.client.logout()
        for url in (self.url, reverse('rental_list')):
            self.assertRedirects(self.client.get(url), f'{reverse("login")}?next={url}')
        response = self.client.post(reverse('login'), {
            'username': 'renter', 'password': 'Ruta!3872x', 'next': self.url,
        })
        self.assertRedirects(response, self.url)

    def test_preview_calculates_without_creating(self):
        response = self.client.post(self.url, self.dates(action='preview'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['quote'], {'days': 3, 'total': Decimal('2250.75')})
        self.assertContains(response, 'Confirmar solicitud')
        self.assertEqual(RentalRequest.objects.count(), 0)

    def test_confirm_saves_pending_and_decimal_total(self):
        response = self.client.post(self.url, self.dates(action='confirm'))
        rental = RentalRequest.objects.get()
        self.assertRedirects(response, reverse('rental_confirmation', args=[rental.pk]))
        self.assertEqual(rental.status, RentalRequest.Status.PENDING)
        self.assertEqual(rental.user, self.user)
        self.assertEqual(rental.vehicle, self.vehicle)
        self.assertEqual(rental.days, 3)
        self.assertEqual(rental.daily_price, Decimal('750.25'))
        self.assertEqual(rental.total_cost, Decimal('2250.75'))
        self.assertIsNotNone(rental.created_at)

    def test_past_start_rejected(self):
        response = self.client.post(self.url, self.dates(
            action='confirm', start_date=(timezone.localdate() - timedelta(days=1)).isoformat(),
        ))
        self.assertContains(response, 'no puede estar en el pasado')
        self.assertFalse(RentalRequest.objects.exists())

    def test_return_equal_or_before_start_rejected(self):
        for end in (self.start, self.start - timedelta(days=1)):
            with self.subTest(end=end):
                response = self.client.post(self.url, self.dates(action='confirm', end_date=end.isoformat()))
                self.assertContains(response, 'debe ser posterior')
                self.assertNotContains(response, 'rental_end_after_start')
                self.assertFalse(RentalRequest.objects.exists())

    def test_missing_and_malformed_dates_rejected(self):
        for data in ({}, {'start_date': 'incorrecta', 'end_date': 'incorrecta'}):
            response = self.client.post(self.url, {**data, 'action': 'confirm'})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(RentalRequest.objects.exists())

    def test_start_today_is_allowed(self):
        rental = self.make_request(start_date=timezone.localdate())
        self.assertGreater(rental.days, 0)

    def test_unavailable_vehicle_blocks_get_and_post(self):
        Vehicle.objects.filter(pk=self.vehicle.pk).update(available=False)
        for response in (self.client.get(self.url), self.client.post(self.url, self.dates(action='confirm'))):
            self.assertContains(response, 'no está disponible')
            self.assertNotContains(response, 'name="action"')
        self.assertFalse(RentalRequest.objects.exists())

    def test_pending_requests_can_overlap(self):
        self.make_request()
        self.make_request(user=self.other)
        self.assertEqual(RentalRequest.objects.filter(status=RentalRequest.Status.PENDING).count(), 2)

    def test_new_request_cannot_overlap_approved(self):
        self.make_request(status=RentalRequest.Status.APPROVED)
        response = self.client.post(self.url, self.dates(action='confirm'))
        self.assertContains(response, 'coincide con estas fechas')
        self.assertEqual(RentalRequest.objects.count(), 1)

    def test_approval_blocks_all_overlap_shapes(self):
        candidates = [
            self.make_request(start_date=start, end_date=end)
            for start, end in (
                (self.start, self.end),
                (self.start + timedelta(days=1), self.end + timedelta(days=1)),
                (self.start - timedelta(days=1), self.end - timedelta(days=1)),
                (self.start - timedelta(days=1), self.end + timedelta(days=1)),
            )
        ]
        self.make_request(status=RentalRequest.Status.APPROVED)
        for rental in candidates:
            with self.subTest(rental=rental.pk):
                rental.status = RentalRequest.Status.APPROVED
                with self.assertRaises(ValidationError):
                    rental.save()
                rental.refresh_from_db()
                self.assertEqual(rental.status, RentalRequest.Status.PENDING)

    def test_adjacent_dates_and_different_vehicle_allowed(self):
        self.make_request(status=RentalRequest.Status.APPROVED)
        self.make_request(start_date=self.end, end_date=self.end + timedelta(days=1),
                          status=RentalRequest.Status.APPROVED)
        self.make_request(start_date=self.start - timedelta(days=1), end_date=self.start,
                          status=RentalRequest.Status.APPROVED)
        vehicle = Vehicle.objects.get(pk=self.vehicle.pk)
        vehicle.pk = None
        vehicle.model = 'Otro'
        vehicle.save()
        self.make_request(vehicle=vehicle, status=RentalRequest.Status.APPROVED)
        self.assertEqual(RentalRequest.objects.count(), 4)

    def test_rejected_does_not_block(self):
        self.make_request(status=RentalRequest.Status.REJECTED)
        self.make_request(status=RentalRequest.Status.APPROVED)
        self.assertEqual(RentalRequest.objects.count(), 2)

    def test_rejecting_approved_releases_dates(self):
        rental = self.make_request(status=RentalRequest.Status.APPROVED)
        rental.status = RentalRequest.Status.REJECTED
        rental.save()
        self.make_request()
        self.assertEqual(RentalRequest.objects.count(), 2)

    def test_price_snapshot_survives_vehicle_price_changes(self):
        rental = self.make_request()
        Vehicle.objects.filter(pk=self.vehicle.pk).update(daily_price=Decimal('999.99'))
        rental.status = RentalRequest.Status.APPROVED
        rental.save()
        rental.refresh_from_db()
        self.assertEqual(rental.daily_price, Decimal('750.25'))
        self.assertEqual(rental.total_cost, Decimal('2250.75'))

    def test_user_sees_only_own_requests_and_confirmation(self):
        own = self.make_request()
        other = self.make_request(user=self.other)
        response = self.client.get(reverse('rental_list'))
        self.assertEqual(list(response.context['rentals']), [own])
        self.assertEqual(self.client.get(reverse('rental_confirmation', args=[other.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('rental_confirmation', args=[own.pk])).status_code, 200)

    def test_posted_owner_status_and_cost_are_ignored(self):
        self.client.post(self.url, self.dates(action='confirm', user=self.other.pk,
                         vehicle=999999, status=RentalRequest.Status.APPROVED,
                         daily_price='0.01', total_cost='0.01'))
        rental = RentalRequest.objects.get()
        self.assertEqual(rental.user, self.user)
        self.assertEqual(rental.vehicle, self.vehicle)
        self.assertEqual(rental.status, RentalRequest.Status.PENDING)
        self.assertEqual(rental.total_cost, Decimal('2250.75'))

    def test_normal_user_cannot_approve(self):
        rental = self.make_request()
        response = self.client.post(reverse('admin:rentals_rentalrequest_change', args=[rental.pk]),
                                    {'status': RentalRequest.Status.APPROVED, '_save': 'Guardar'})
        self.assertEqual(response.status_code, 302)
        rental.refresh_from_db()
        self.assertEqual(rental.status, RentalRequest.Status.PENDING)

    def test_admin_approval_rechecks_overlap_and_rejects(self):
        first = self.make_request()
        second = self.make_request(user=self.other)
        self.client.force_login(self.admin)
        first_url = reverse('admin:rentals_rentalrequest_change', args=[first.pk])
        second_url = reverse('admin:rentals_rentalrequest_change', args=[second.pk])
        self.assertEqual(self.client.post(first_url, {'status': RentalRequest.Status.APPROVED, '_save': 'Guardar'}).status_code, 302)
        self.assertContains(self.client.post(second_url, {'status': RentalRequest.Status.APPROVED, '_save': 'Guardar'}), 'coincide con estas fechas')
        second.refresh_from_db()
        self.assertEqual(second.status, RentalRequest.Status.PENDING)
        self.assertEqual(self.client.post(second_url, {'status': RentalRequest.Status.REJECTED, '_save': 'Guardar'}).status_code, 302)
        second.refresh_from_db()
        self.assertEqual(second.status, RentalRequest.Status.REJECTED)

    def test_admin_cannot_change_history_or_add_or_delete(self):
        rental = self.make_request()
        self.client.force_login(self.admin)
        self.client.post(reverse('admin:rentals_rentalrequest_change', args=[rental.pk]), {
            'user': self.other.pk, 'vehicle': 99999, 'daily_price': '1', 'total_cost': '1',
            'start_date': '2000-01-01', 'end_date': '2000-01-02',
            'status': RentalRequest.Status.APPROVED, '_save': 'Guardar',
        })
        rental.refresh_from_db()
        self.assertEqual(rental.user, self.user)
        self.assertEqual(rental.vehicle, self.vehicle)
        self.assertEqual(rental.start_date, self.start)
        self.assertEqual(rental.end_date, self.end)
        self.assertEqual(rental.daily_price, Decimal('750.25'))
        self.assertEqual(rental.total_cost, Decimal('2250.75'))
        self.assertEqual(self.client.get(reverse('admin:rentals_rentalrequest_add')).status_code, 403)
        self.assertEqual(self.client.post(reverse('admin:rentals_rentalrequest_delete', args=[rental.pk])).status_code, 403)

    def test_related_history_is_protected_from_deletion(self):
        self.make_request()
        with self.assertRaises(ProtectedError):
            self.vehicle.delete()
        with self.assertRaises(ProtectedError):
            self.user.delete()

    def test_missing_vehicle_and_empty_list(self):
        self.assertEqual(self.client.get(reverse('rental_create', args=[999999])).status_code, 404)
        self.assertContains(self.client.get(reverse('rental_list')), 'Aún no tienes solicitudes')

    def test_vehicle_detail_links_to_request(self):
        url = reverse('vehicle_detail', args=[self.vehicle.pk])
        self.assertContains(self.client.get(url), f'href="{self.url}"')
        Vehicle.objects.filter(pk=self.vehicle.pk).update(available=False)
        self.assertNotContains(self.client.get(url), f'href="{self.url}"')

    def test_csrf_required(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url, self.dates(action='confirm')).status_code, 403)
