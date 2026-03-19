from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.models.schedule import Schedule


class AppointmentService:
    @staticmethod
    def book(*, patient_id: int, schedule_id: int) -> Appointment:
        schedule = db.session.get(Schedule, schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        if not schedule.is_available:
            raise ValueError("This slot is not available")

        appt = Appointment(
            patient_id=patient_id,
            doctor_id=schedule.doctor_id,
            schedule_id=schedule.id,
            status=AppointmentStatus.PENDING,
        )
        db.session.add(appt)
        schedule.is_available = False
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("This slot has been booked") from e
        return appt

    @staticmethod
    def list_for_patient(*, patient_id: int) -> list[Appointment]:
        stmt = (
            db.select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .order_by(Appointment.created_at.desc())
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def list_for_doctor(*, doctor_id: int) -> list[Appointment]:
        stmt = db.select(Appointment).where(Appointment.doctor_id == doctor_id).order_by(Appointment.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def update_status(*, appointment: Appointment, status: AppointmentStatus) -> Appointment:
        if status == AppointmentStatus.CANCELLED:
            appointment.schedule.is_available = True
        appointment.status = status
        db.session.commit()
        return appointment

