import unittest
from datetime import date, time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config

from app import create_app
from app.extensions import db
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus, UserRole
from app.models.hospital import Hospital
from app.models.schedule import Schedule
from app.models.user import User
from app.services.appointment_service import AppointmentService


class TestAppointmentBooking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_db_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.engine.dispose()
        cls.ctx.pop()
        Config.SQLALCHEMY_DATABASE_URI = cls._old_db_uri

    def setUp(self):
        db.drop_all()
        db.create_all()

    def _create_user(self, username: str, role: UserRole, phone: str) -> User:
        user = User(username=username, role=role, email=f"{username}@example.com", phone=phone)
        user.set_password("123456")
        db.session.add(user)
        db.session.flush()
        return user

    def _create_doctor(self, username: str, hospital_name: str) -> Doctor:
        doctor_user = self._create_user(username, UserRole.DOCTOR, "0900999999")
        hospital = Hospital(name=hospital_name)
        db.session.add(hospital)
        db.session.flush()
        doctor = Doctor(
            user_id=doctor_user.id,
            specialty="Noi khoa",
            hospital_id=hospital.id,
            experience_years=5,
        )
        db.session.add(doctor)
        db.session.flush()
        return doctor

    def _create_slot(self, doctor: Doctor, slot_date: date, start: time, end: time, is_available: bool) -> Schedule:
        slot = Schedule(
            doctor_id=doctor.id,
            date=slot_date,
            start_time=start,
            end_time=end,
            is_available=is_available,
        )
        db.session.add(slot)
        db.session.commit()
        return slot

    def test_case_1_book_success(self):
        patient = self._create_user("patient_a", UserRole.PATIENT, "0901111111")
        doctor = self._create_doctor("doctor_a", "Benh vien Dat Lich")
        slot = self._create_slot(doctor, date(2026, 5, 10), time(9, 0), time(10, 0), True)

        appt = AppointmentService.book(
            patient_id=patient.id,
            schedule_id=slot.id,
            booking_for="self",
            contact_fullname="patient_a",
            contact_email=patient.email,
            contact_phone=patient.phone,
            symptoms="dau dau",
        )
        self.assertTrue(appt.id is not None)
        self.assertEqual(AppointmentStatus.PENDING, appt.status)
        self.assertFalse(slot.is_available)

    def test_case_2_book_fail_when_slot_unavailable(self):
        patient = self._create_user("patient_b", UserRole.PATIENT, "0902222222")
        doctor = self._create_doctor("doctor_b", "Benh vien B")
        slot = self._create_slot(doctor, date(2026, 5, 11), time(10, 0), time(11, 0), False)

        with self.assertRaises(ValueError):
            AppointmentService.book(
                patient_id=patient.id,
                schedule_id=slot.id,
                booking_for="self",
                contact_fullname="patient_b",
                contact_email=patient.email,
                contact_phone=patient.phone,
                symptoms="sot",
            )

    def test_case_3a_relative_different_phone_allows_overlap(self):
        patient = self._create_user("patient_rel_a", UserRole.PATIENT, "0904444444")
        doctor = self._create_doctor("doctor_rel_a", "Benh vien Rel A")
        slot_1 = self._create_slot(doctor, date(2026, 5, 13), time(9, 0), time(10, 0), True)
        slot_2 = self._create_slot(doctor, date(2026, 5, 13), time(9, 30), time(10, 30), True)

        AppointmentService.book(
            patient_id=patient.id,
            schedule_id=slot_1.id,
            booking_for="relative",
            contact_fullname="Nguyen Van A",
            contact_email="a@example.com",
            contact_phone="0911111111",
            symptoms="ho",
        )
        appt_b = AppointmentService.book(
            patient_id=patient.id,
            schedule_id=slot_2.id,
            booking_for="relative",
            contact_fullname="Tran Van B",
            contact_email="b@example.com",
            contact_phone="0922222222",
            symptoms="sot",
        )
        self.assertTrue(appt_b.id)

    def test_case_3b_self_then_relative_different_phone_allowed(self):
        patient = self._create_user("patient_rel_b", UserRole.PATIENT, "0905555555")
        doctor = self._create_doctor("doctor_rel_b", "Benh vien Rel B")
        slot_1 = self._create_slot(doctor, date(2026, 5, 14), time(8, 0), time(9, 0), True)
        slot_2 = self._create_slot(doctor, date(2026, 5, 14), time(8, 30), time(9, 30), True)

        AppointmentService.book(
            patient_id=patient.id,
            schedule_id=slot_1.id,
            booking_for="self",
            contact_fullname="patient_rel_b",
            contact_email=patient.email,
            contact_phone=patient.phone,
            symptoms="dau",
        )
        appt_rel = AppointmentService.book(
            patient_id=patient.id,
            schedule_id=slot_2.id,
            booking_for="relative",
            contact_fullname="Nguoi than",
            contact_email="than@example.com",
            contact_phone="0933333333",
            symptoms="met",
        )
        self.assertTrue(appt_rel.id)

    def test_case_3c_relative_same_phone_overlap_blocked(self):
        patient = self._create_user("patient_rel_c", UserRole.PATIENT, "0906666666")
        doctor = self._create_doctor("doctor_rel_c", "Benh vien Rel C")
        slot_1 = self._create_slot(doctor, date(2026, 5, 15), time(10, 0), time(11, 0), True)
        slot_2 = self._create_slot(doctor, date(2026, 5, 15), time(10, 30), time(11, 30), True)

        AppointmentService.book(
            patient_id=patient.id,
            schedule_id=slot_1.id,
            booking_for="relative",
            contact_fullname="Cung SDT",
            contact_email="c@example.com",
            contact_phone="0944444444",
            symptoms="ho",
        )
        with self.assertRaises(ValueError):
            AppointmentService.book(
                patient_id=patient.id,
                schedule_id=slot_2.id,
                booking_for="relative",
                contact_fullname="Cung SDT lan 2",
                contact_email="c2@example.com",
                contact_phone="09444 44444",
                symptoms="ho tiep",
            )

    def test_case_3d_rebook_cancelled_slot_for_relative(self):
        patient = self._create_user("patient_rebook", UserRole.PATIENT, "0908888888")
        doctor = self._create_doctor("doctor_rebook", "Benh vien Rebook")
        slot = self._create_slot(doctor, date(2026, 5, 16), time(11, 0), time(12, 0), True)

        self_appt = AppointmentService.book(
            patient_id=patient.id,
            schedule_id=slot.id,
            booking_for="self",
            contact_fullname="patient_rebook",
            contact_email=patient.email,
            contact_phone=patient.phone,
            symptoms="lan 1",
        )
        AppointmentService.update_status(appointment=self_appt, status=AppointmentStatus.CANCELLED)
        self.assertTrue(slot.is_available)

        relative_appt = AppointmentService.book(
            patient_id=patient.id,
            schedule_id=slot.id,
            booking_for="relative",
            contact_fullname="Nguoi than moi",
            contact_email="than@example.com",
            contact_phone="0977777777",
            symptoms="lan 2",
        )
        self.assertEqual(self_appt.id, relative_appt.id)
        self.assertEqual("relative", relative_appt.booking_for)
        self.assertEqual(AppointmentStatus.PENDING, relative_appt.status)
        self.assertFalse(slot.is_available)

    def test_case_3_book_fail_when_duplicate_time(self):
        patient = self._create_user("patient_c", UserRole.PATIENT, "0903333333")
        doctor = self._create_doctor("doctor_c", "Benh vien C")
        slot_1 = self._create_slot(doctor, date(2026, 5, 12), time(8, 0), time(9, 0), True)
        slot_2 = self._create_slot(doctor, date(2026, 5, 12), time(8, 30), time(9, 30), True)

        AppointmentService.book(
            patient_id=patient.id,
            schedule_id=slot_1.id,
            booking_for="self",
            contact_fullname="patient_c",
            contact_email=patient.email,
            contact_phone=patient.phone,
            symptoms="ho",
        )

        with self.assertRaises(ValueError):
            AppointmentService.book(
                patient_id=patient.id,
                schedule_id=slot_2.id,
                booking_for="self",
                contact_fullname="patient_c",
                contact_email=patient.email,
                contact_phone=patient.phone,
                symptoms="ho tiep",
            )


if __name__ == "__main__":
    unittest.main()
