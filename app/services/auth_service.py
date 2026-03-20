from flask_login import login_user, logout_user

from app.extensions import db
from app.models.doctor import Doctor
from app.models.hospital import Hospital
from app.models.enums import UserRole
from app.models.user import User


class AuthService:
    @staticmethod
    def register_user(
        *,
        username: str,
        password: str,
        role: UserRole,
        specialty: str | None = None,
        hospital_name: str | None = None,
        description: str | None = None,
        experience_years: int | None = None,
    ) -> User:
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role == UserRole.DOCTOR:
            if not specialty:
                raise ValueError("Specialty is required for DOCTOR")
            hospital_id: int | None = None
            hospital_name_value = (hospital_name or "").strip()
            if hospital_name_value:
                hospital = db.session.execute(
                    db.select(Hospital).where(Hospital.name == hospital_name_value)
                ).scalar_one_or_none()
                if not hospital:
                    hospital = Hospital(name=hospital_name_value)
                    db.session.add(hospital)
                    db.session.flush()
                hospital_id = hospital.id
            doc = Doctor(
                user_id=user.id,
                specialty=specialty.strip(),
                hospital_id=hospital_id,
                description=(description or "").strip() or None,
                experience_years=int(experience_years or 0),
            )
            db.session.add(doc)

        db.session.commit()
        return user

    @staticmethod
    def authenticate(*, username: str, password: str) -> User | None:
        user = db.session.execute(db.select(User).where(User.username == username)).scalar_one_or_none()
        if not user:
            return None
        if not user.check_password(password):
            return None
        return user

    @staticmethod
    def login(user: User) -> None:
        login_user(user)

    @staticmethod
    def logout() -> None:
        logout_user()

