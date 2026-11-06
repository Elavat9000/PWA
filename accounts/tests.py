from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def test_home_and_forms(self):
        for name in ('home', 'signup', 'login'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_registration_login_logout_and_permissions(self):
        response = self.client.post(reverse('signup'), {
            'username': 'viajera', 'password1': 'ViajeSeguro!384',
            'password2': 'ViajeSeguro!384',
        })
        self.assertRedirects(response, reverse('home'))
        user = User.objects.get(username='viajera')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.post(reverse('login'), {
            'username': 'viajera', 'password': 'ViajeSeguro!384',
        }), reverse('home'))

    def test_invalid_registration_and_login(self):
        response = self.client.post(reverse('signup'), {
            'username': 'x', 'password1': '123', 'password2': '456',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        response = self.client.post(reverse('login'), {'username': 'x', 'password': 'bad'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_csrf_required(self):
        from django.test import Client
        self.assertEqual(Client(enforce_csrf_checks=True).post(reverse('signup'), {}).status_code, 403)
