from datetime import date

from sqlalchemy import extract, func, or_, select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.models.schedule import Schedule
from app.services.mail_service import notify_patient_appointment_status_changed


class AppointmentService:
    @staticmethod
    def parse_list_filters(
        *,
        month: int | None,
        year: int | None,
        status_value: str | None,
    ) -> tuple[int | None, int | None, AppointmentStatus | None]:
        parsed_month = month if month is not None and 1 <= month <= 12 else None
        parsed_year = year if year is not None and 2000 <= year <= 2100 else None
        raw_status = (status_value or "").strip().upper()
        parsed_status = None
        if raw_status in {s.value for s in AppointmentStatus}:
            parsed_status = AppointmentStatus(raw_status)
        return parsed_month, parsed_year, parsed_status

    @staticmethod
    def _patient_scope_condition(*, patient_id: int):
        from app.models.user import User

        patient = db.session.get(User, patient_id)
        phone_value = (getattr(patient, "phone", "") or "").strip() if patient else ""
        return or_(
            Appointment.patient_id == patient_id,
            Appointment.contact_phone == phone_value if phone_value else False,
        )

    @staticmethod
    def _apply_schedule_date_filters(stmt, *, month: int | None, year: int | None):
        if month is None and year is None:
            return stmt
        stmt = stmt.join(Schedule, Schedule.id == Appointment.schedule_id)
        if month is not None:
            stmt = stmt.where(extract("month", Schedule.date) == month)
        if year is not None:
            stmt = stmt.where(extract("year", Schedule.date) == year)
        return stmt

    @staticmethod
    def schedule_years_for_patient(*, patient_id: int) -> list[int]:
        scope = AppointmentService._patient_scope_condition(patient_id=patient_id)
        stmt = (
            select(func.distinct(extract("year", Schedule.date)))
            .select_from(Appointment)
            .join(Schedule, Schedule.id == Appointment.schedule_id)
            .where(scope)
            .order_by(extract("year", Schedule.date).desc())
        )
        years = [int(y) for y in db.session.execute(stmt).scalars().all() if y is not None]
        if not years:
            years = [date.today().year]
        return years

    @staticmethod
    def schedule_years_for_doctor(*, doctor_id: int) -> list[int]:
        stmt = (
            select(func.distinct(extract("year", Schedule.date)))
            .select_from(Appointment)
            .join(Schedule, Schedule.id == Appointment.schedule_id)
            .where(Appointment.doctor_id == doctor_id)
            .order_by(extract("year", Schedule.date).desc())
        )
        years = [int(y) for y in db.session.execute(stmt).scalars().all() if y is not None]
        if not years:
            years = [date.today().year]
        return years

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

        existing_appt = db.session.execute(
            db.select(Appointment).where(Appointment.schedule_id == schedule_id)
        ).scalar_one_or_none()

        if existing_appt:
            if existing_appt.status != AppointmentStatus.CANCELLED:
                raise ValueError("This slot has been booked")
        elif not schedule.is_available:
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

        if existing_appt and existing_appt.status == AppointmentStatus.CANCELLED:
            existing_appt.patient_id = patient_id
            existing_appt.doctor_id = schedule.doctor_id
            existing_appt.booking_for = (booking_for or "self").strip().lower()
            existing_appt.contact_fullname = contact_fullname
            existing_appt.contact_email = contact_email
            existing_appt.contact_phone = contact_phone
            existing_appt.symptoms = symptoms
            existing_appt.status = status
            schedule.is_available = False
            db.session.commit()
            return existing_appt

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
    def _normalize_phone(phone: str | None) -> str:
        """Chuẩn hóa SĐT để so khớp (chỉ giữ chữ số)."""
        return "".join(ch for ch in (phone or "").strip() if ch.isdigit())

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
        booking_for = (booking_for or "").strip().lower()
        stmt = (
            db.select(Appointment.contact_phone)
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
            return db.session.execute(stmt.limit(1)).scalar_one_or_none() is not None

        if booking_for != "relative":
            return False

        norm_phone = AppointmentService._normalize_phone(contact_phone)
        if not norm_phone:
            return False

        stmt = stmt.where(
            Appointment.patient_id == patient_id,
            Appointment.booking_for == "relative",
        )
        existing_phones = db.session.execute(stmt).scalars().all()
        return any(AppointmentService._normalize_phone(p) == norm_phone for p in existing_phones)

    @staticmethod
    def list_for_patient(
        *,
        patient_id: int,
        month: int | None = None,
        year: int | None = None,
        status: AppointmentStatus | None = None,
    ) -> list[Appointment]:
        stmt = db.select(Appointment).where(AppointmentService._patient_scope_condition(patient_id=patient_id))
        stmt = AppointmentService._apply_schedule_date_filters(stmt, month=month, year=year)
        if status is not None:
            stmt = stmt.where(Appointment.status == status)
        stmt = stmt.order_by(Appointment.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def list_for_doctor(
        *,
        doctor_id: int,
        month: int | None = None,
        year: int | None = None,
        status: AppointmentStatus | None = None,
    ) -> list[Appointment]:
        stmt = db.select(Appointment).where(Appointment.doctor_id == doctor_id)
        stmt = AppointmentService._apply_schedule_date_filters(stmt, month=month, year=year)
        if status is not None:
            stmt = stmt.where(Appointment.status == status)
        stmt = stmt.order_by(Appointment.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def update_status(*, appointment: Appointment, status: AppointmentStatus) -> Appointment:
        previous_status = appointment.status
        if status == AppointmentStatus.CANCELLED:
            appointment.schedule.is_available = True
        appointment.status = status
        db.session.commit()
        notify_patient_appointment_status_changed(appointment=appointment, previous_status=previous_status)
        return appointment

