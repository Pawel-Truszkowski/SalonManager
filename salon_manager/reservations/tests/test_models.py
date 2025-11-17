from datetime import date, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone
from reservations.models import Reservation, ReservationRequest, WorkDay

from .base_test import BaseTestCase


class WorkDayModelTest(BaseTestCase):
    def test_workday_creation(self):
        self.assertEqual(self.workday.employee, self.employee1)
        self.assertEqual(str(self.workday), f"{self.employee1} - {self.workday.date}")

    def test_related_name(self):
        self.assertEqual(self.employee1.work_day.count(), 1)

    def test_end_time_before_start_time_raises_error(self):
        workday = WorkDay(
            date=date(2025, 1, 15),
            start_time=time(17, 0),
            end_time=time(9, 0),
            employee=self.employee1,
        )
        with self.assertRaises(ValidationError) as context:
            workday.save()

        self.assertIn("end_time", context.exception.message_dict)

    def test_end_time_equal_start_time_raises_error(self):
        workday = WorkDay(
            date=date(2025, 1, 15),
            start_time=time(9, 0),
            end_time=time(9, 0),
            employee=self.employee1,
        )
        with self.assertRaises(ValidationError):
            workday.save()

    def test_valid_time_range_saves_successfully(self):
        workday = WorkDay.objects.create(
            date=date(2025, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            employee=self.employee1,
        )
        self.assertIsNotNone(workday.pk)


class ReservationRequestModelTest(BaseTestCase):
    def test_reservation_request_creation(self):
        reservation_request = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
        )
        self.assertIsNotNone(reservation_request.pk)
        self.assertEqual(reservation_request.employee, self.employee1)
        self.assertEqual(reservation_request.service, self.service1)
        self.assertEqual(reservation_request.service.category, self.service_category1)

    def test_str_method(self):
        reservation_request = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
        )
        expexted = f"{date.today()} - 09:00:00 to 10:00:00 - {self.service1.name}"

        self.assertEqual(str(reservation_request), expexted)

    def test_auto_generate_id_request(self):
        reservation_request = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
        )
        self.assertIsNotNone(reservation_request.id_request)
        self.assertIn(str(self.service1.id), reservation_request.id_request)

    def test_id_request_not_overwritten_if_exists(self):
        id_request = "1234567890"
        reservation_request = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
            id_request=id_request,
        )
        self.assertEqual(reservation_request.id_request, id_request)

    def test_auto_set_expires_at(self):
        before = timezone.now()
        reservation_request = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
        )
        after = timezone.now()

        expected_min = before + timedelta(minutes=15)
        expected_max = after + timedelta(minutes=15)
        self.assertLessEqual(reservation_request.expires_at, expected_max)
        self.assertGreaterEqual(reservation_request.expires_at, expected_min)

    def test_is_expired_return_false_for_future_expiry(self):
        reservation_request = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertFalse(reservation_request.is_expired())

    def test_is_expired_return_true_for_past_expiry(self):
        reservation_request = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
            expires_at=timezone.now() - timedelta(minutes=10),
        )
        self.assertTrue(reservation_request.is_expired())

    def test_get_service_name(self):
        reservation = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            service=self.service1,
            employee=self.employee1,
        )
        self.assertEqual(reservation.get_service_name(), "Manicure classic")

    def test_created_at_and_updated_at_auto_set(self):
        reservation = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            service=self.service1,
            employee=self.employee1,
        )
        self.assertIsNotNone(reservation.created_at)
        self.assertIsNotNone(reservation.updated_at)

    def test_start_time_after_end_time_rises_error(self):
        reservation = ReservationRequest.objects.create(
            date=date.today(),
            start_time=time(11, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
        )

        with self.assertRaises(ValidationError) as context:
            reservation.clean()
        self.assertIn("Start time must be before end time", str(context.exception))

    def test_start_time_equal_end_time_raises_error(self):
        reservation = ReservationRequest(
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
        )
        with self.assertRaises(ValidationError) as context:
            reservation.clean()
        self.assertIn(
            "Start time and end time cannot be the same", str(context.exception)
        )

    def test_duration_exceeds_service_duration_raises_error(self):
        reservation = ReservationRequest(
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            service=self.service1,
            employee=self.employee1,
        )
        with self.assertRaises(ValidationError) as context:
            reservation.clean()
        self.assertIn(
            "Duration cannot exceed the service duration", str(context.exception)
        )

    def test_past_date_raises_error(self):
        past_date = date.today() - timedelta(days=1)
        reservation = ReservationRequest(
            date=past_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            service=self.service1,
            employee=self.employee1,
        )
        with self.assertRaises(ValidationError) as context:
            reservation.clean()
        self.assertIn("Date cannot be in the past", str(context.exception))


class ReservationModelTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.reservation_request = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            service=self.service1,
            employee=self.employee1,
        )

    def test_create_reservation_with_customer(self):
        reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.reservation_request,
            name="Georges Hammond",
            email="georges.s.hammond@test.com",
            phone="+48611711911",
        )
        self.assertIsNotNone(reservation.pk)
        self.assertEqual(reservation.customer, self.users["client1"])
        self.assertEqual(reservation.status, "PENDING")

    def test_create_reservation_without_customer(self):
        reservation = Reservation.objects.create(
            customer=None,
            reservation_request=self.reservation_request,
            name="John Doe",
            email="john.doe@test.com",
            phone="+48123456789",
        )
        self.assertIsNone(reservation.customer)
        self.assertEqual(reservation.name, "John Doe")

    def test_str_method_with_customer(self):
        reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.reservation_request,
            name="Georges Hammond",
        )
        str_repr = str(reservation)
        self.assertIn("georges.hammond", str_repr)
        self.assertIn(str(self.reservation_request.date), str_repr)

    def test_str_method_without_customer(self):
        reservation = Reservation.objects.create(
            customer=None,
            reservation_request=self.reservation_request,
            name="John Doe",
        )
        str_repr = str(reservation)
        self.assertIn("John Doe", str_repr)

    def test_auto_generate_id_request(self):
        reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.reservation_request,
            name="Georges Hammond",
        )
        self.assertIsNotNone(reservation.id_request)
        self.assertIn(str(self.service1.id), reservation.id_request)

    def test_id_request_not_overwritten_if_exists(self):
        custom_id = "CUSTOM123"
        reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.reservation_request,
            name="Georges Hammond",
            id_request=custom_id,
        )
        self.assertEqual(reservation.id_request, custom_id)

    def test_status_choices(self):
        statuses = ["PENDING", "CONFIRMED", "CANCELLED", "PAST"]
        for status in statuses:
            request = ReservationRequest.objects.create(
                date=date.today() + timedelta(days=1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                service=self.service1,
                employee=self.employee1,
            )
            reservation = Reservation.objects.create(
                customer=self.users["client1"],
                reservation_request=request,
                name="Test User",
                status=status,
            )
            self.assertEqual(reservation.status, status)

    def test_default_status_is_pending(self):
        reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.reservation_request,
            name="Georges Hammond",
        )
        self.assertEqual(reservation.status, "PENDING")

    def test_one_to_one_relationship_with_reservation_request(self):
        Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.reservation_request,
            name="First Reservation",
        )

        with self.assertRaises(Exception):
            Reservation.objects.create(
                customer=self.users["client2"],
                reservation_request=self.reservation_request,
                name="Second Reservation",
            )

    def test_created_at_and_updated_at(self):
        reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.reservation_request,
            name="Georges Hammond",
        )
        self.assertIsNotNone(reservation.created_at)
        self.assertIsNotNone(reservation.updated_at)


class ReservationGettersTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.reservation_request = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            service=self.service1,
            employee=self.employee1,
        )
        self.reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.reservation_request,
            name="Georges Hammond",
        )

    def test_get_date(self):
        expected_date = date.today() + timedelta(days=1)
        self.assertEqual(self.reservation.get_date(), expected_date)

    def test_get_start_time(self):
        self.assertEqual(self.reservation.get_start_time(), time(10, 0))

    def test_get_end_time(self):
        self.assertEqual(self.reservation.get_end_time(), time(11, 0))

    def test_get_service(self):
        self.assertEqual(self.reservation.get_service(), self.service1)

    def test_get_service_name(self):
        self.assertEqual(self.reservation.get_service_name(), "Manicure classic")

    def test_get_service_duration(self):
        self.assertEqual(self.reservation.get_service_duration(), 60)

    def test_get_employee_name(self):
        self.assertEqual(self.reservation.get_employee_name(), "Daniel")

    def test_get_employee_name_when_no_employee(self):
        request_no_employee = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=2),
            start_time=time(14, 0),
            end_time=time(15, 0),
            service=self.service1,
            employee=None,
        )
        reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=request_no_employee,
            name="Test User",
        )
        self.assertEqual(reservation.get_employee_name(), "")

    def test_get_employee(self):
        self.assertEqual(self.reservation.get_employee(), self.employee1)

    def test_get_employee_when_none(self):
        request_no_employee = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=2),
            start_time=time(14, 0),
            end_time=time(15, 0),
            service=self.service1,
            employee=None,
        )
        reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=request_no_employee,
            name="Test User",
        )
        self.assertIsNone(reservation.get_employee())

    def test_get_service_price(self):
        self.assertEqual(self.reservation.get_service_price(), Decimal("200"))

    def test_get_customer_name(self):
        self.assertEqual(self.reservation.get_customer_name(), "Georges Hammond")
