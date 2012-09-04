from django.test import TestCase
from models import Reservation, SimpleReservation, Holiday
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings
# from django.conf import settings
import json
from django.db import models
import datetime as dt
from datetime import datetime
from . import update_model


class ExtendedReservation(Reservation):
    """Some extra data for the basic model"""
    extra_data_required = models.CharField(max_length=100)


class TestLoggedIn(TestCase):
    code = "foo"
    reservtion_data = {
        "simple": {"year": 2032, "month": 12, "day": 12},
    }

    def setUp(self):
        # Create test user in DB
        from django.contrib.auth.models import User
        user = User.objects.create_user('fred', 'fred@astor.com', 'astor')
        user.save()
        self.client = Client()
        self.client.login(username='fred', password='astor')

        # from datetime import datetime
        self.reservtion_data['late'] = {"year": datetime.now().year,
                                        "month": datetime.now().month,
                                        "day": datetime.now().day}
        # By default use the default SimpleReservation model
        update_model(SimpleReservation)

    def test_not_authorized(self):
        """Not logged in user tries to make a reservation"""
        self.client.logout()
        response = self.client.post(reverse('reservations_reservation'), self.reservtion_data['simple'], follow=False)
        self.assertTrue('/accounts/login/' in response['Location'])

    @override_settings(RESERVATIONS_PER_DAY=2)
    def test_above_threshold(self):
        """User should not be able to make more than RESERVATIONS_PER_DAY reservation"""
        response = self.client.post(reverse('reservations_reservation'), self.reservtion_data['simple'], follow=True)
        # print "RESPONSE", response.content
        # print "response.redirect_chain", response.redirect_chain
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('reservations_reservation'), self.reservtion_data['simple'], follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('reservations_reservation'), self.reservtion_data['simple'], follow=True)
        # print "Number of reservations", SimpleReservation.objects.all().count(), reverse('reservations_reservation')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(SimpleReservation.objects.all().count(), 2)

    def test_reservation(self):
        """Successfully create reservation"""
        response = self.client.post(reverse('reservations_reservation'), self.reservtion_data['simple'], follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SimpleReservation.objects.all().count(), 1)

    def test_cancel_reservation(self):
        """Test cancallation of reservation"""
        # First, create a reservation
        response = self.client.post(reverse('reservations_reservation'), self.reservtion_data['simple'], follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SimpleReservation.objects.all().count(), 1)
        reservation_id = json.loads(response.content)['reservation']["id"]
        # Then, cancel it
        response = self.client.delete(reverse('reservations_reservation'), {"id": reservation_id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SimpleReservation.objects.all().count(), 0)
        # Create reservation for less than 48h in future
        response = self.client.post(reverse('reservations_reservation'), self.reservtion_data['late'], follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SimpleReservation.objects.all().count(), 1)
        reservation_id = json.loads(response.content)['reservation']["id"]
        # Try to cancel it (error!)
        response = self.client.delete(reverse('reservations_reservation'), {"id": reservation_id}, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(SimpleReservation.objects.all().count(), 1)

    def test_extra_data_form(self):
        """User should not be able to make a reservation without required fields"""
        update_model(ExtendedReservation)
        response = self.client.post(reverse('reservations_reservation'), self.reservtion_data['simple'], follow=True)
        self.assertTrue("errors" in response.content)
        self.assertEqual(ExtendedReservation.objects.all().count(), 0)
        # Provide some extra data
        extendedData = self.reservtion_data['simple'].copy()
        extendedData['extra_data_required'] = "foo"
        response = self.client.post(reverse('reservations_reservation'), extendedData, follow=True)
        self.assertFalse("errors" in response.content)
        self.assertEqual(ExtendedReservation.objects.all().count(), 1)

    def test_holiday(self):
        """User should not be able to make a reservation on holiday day"""
        # Create a holiday
        holiday = Holiday(name="Test Holiday", active=True, date=dt.date(2032, 12, 13))
        holiday.save()
        # Try to make a reservation
        holiday_date = {"year": 2032, "month": 12, "day": 13}
        response = self.client.post(reverse('reservations_reservation'), holiday_date, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(SimpleReservation.objects.all().count(), 0)
        # Disable holiday and re-try to make a reservation
        holiday.active = False
        holiday.save()
        response = self.client.post(reverse('reservations_reservation'), holiday_date, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SimpleReservation.objects.all().count(), 1)
