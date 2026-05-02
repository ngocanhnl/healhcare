import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config

from app import create_app
from app.extensions import db
from app.models.doctor import Doctor
from app.models.enums import UserRole
from app.models.hospital import Hospital
from app.services.auth_service import AuthService


class TestAuthRegistration(unittest.TestCase):
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

    def test_doctor_register_fails_without_hospital(self):
        with self.assertRaises(ValueError):
            AuthService.register_user(
                username="doctor_no_hospital",
                email="doctor_no_hospital@example.com",
                phone="0905000001",
                password="123456",
                role=UserRole.DOCTOR,
                specialty="Noi khoa",
                hospital_id=None,
            )

    def test_doctor_register_fails_with_invalid_hospital(self):
        with self.assertRaises(ValueError):
            AuthService.register_user(
                username="doctor_invalid_hospital",
                email="doctor_invalid_hospital@example.com",
                phone="0905000002",
                password="123456",
                role=UserRole.DOCTOR,
                specialty="Noi khoa",
                hospital_id=9999,
            )

    def test_doctor_register_success_with_existing_hospital(self):
        hospital = Hospital(name="Benh vien A")
        db.session.add(hospital)
        db.session.commit()

        user = AuthService.register_user(
            username="doctor_ok",
            email="doctor_ok@example.com",
            phone="0905000003",
            password="123456",
            role=UserRole.DOCTOR,
            specialty="Noi khoa",
            hospital_id=hospital.id,
        )
        doctor = db.session.execute(db.select(Doctor).where(Doctor.user_id == user.id)).scalar_one_or_none()

        self.assertIsNotNone(doctor)
        self.assertEqual(hospital.id, doctor.hospital_id)


if __name__ == "__main__":
    unittest.main()
