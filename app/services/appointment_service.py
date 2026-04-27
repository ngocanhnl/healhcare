from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.models.schedule import Schedule


class AppointmentService:
    @staticmethod
    def book(
        *,
        patient_id: int,
        schedule_id: int,
        booking_for: str,
        contact_fullname: str,
        contact_email: str | None,
        contact_phone: str,
        symptoms: str | None,
        status: AppointmentStatus = AppointmentStatus.PENDING,
    ) -> Appointment:
        schedule = db.session.get(Schedule, schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        if not schedule.is_available:
            raise ValueError("This slot is not available")
        if AppointmentService.has_duplicate_person_booking(
            patient_id=patient_id,
            booking_for=booking_for,
            contact_email=contact_email,
            contact_phone=contact_phone,
            date_value=schedule.date,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
        ):
            raise ValueError("This person already has another appointment at this time")

        appt = Appointment(
            patient_id=patient_id,
            doctor_id=schedule.doctor_id,
            schedule_id=schedule.id,
            booking_for=booking_for,
            contact_fullname=contact_fullname,
            contact_email=contact_email,
            contact_phone=contact_phone,
            symptoms=symptoms,
            status=status,
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
    def has_duplicate_person_booking(
        *,
        patient_id: int,
        booking_for: str,
        contact_email: str | None,
        contact_phone: str,
        date_value,
        start_time,
        end_time,
    ) -> bool:
        stmt = (
            db.select(Appointment.id)
            .join(Schedule, Schedule.id == Appointment.schedule_id)
            .where(
                Schedule.date == date_value,
                Schedule.start_time < end_time,
                Schedule.end_time > start_time,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
            )
        )
        if booking_for == "self":
            stmt = stmt.where(Appointment.patient_id == patient_id, Appointment.booking_for == "self")
        else:
            email_value = (contact_email or "").strip()
            if email_value:
                stmt = stmt.where(
                    Appointment.booking_for == "relative",
                    Appointment.contact_phone == contact_phone,
                    Appointment.contact_email == email_value,
                )
            else:
                stmt = stmt.where(Appointment.booking_for == "relative", Appointment.contact_phone == contact_phone)
        existing_id = db.session.execute(stmt.limit(1)).scalar_one_or_none()
        return existing_id is not None

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

