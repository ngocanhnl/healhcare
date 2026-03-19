from datetime import date, time

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.schedule import Schedule


class ScheduleService:
    @staticmethod
    def list_doctor_schedules(*, doctor_id: int) -> list[Schedule]:
        stmt = db.select(Schedule).where(Schedule.doctor_id == doctor_id).order_by(
            Schedule.date.desc(), Schedule.start_time.desc()
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def create_schedule(
        *, doctor_id: int, date_value: date, start_time_value: time, end_time_value: time, is_available: bool
    ) -> Schedule:
        schedule = Schedule(
            doctor_id=doctor_id,
            date=date_value,
            start_time=start_time_value,
            end_time=end_time_value,
            is_available=is_available,
        )
        db.session.add(schedule)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("This time slot already exists") from e
        return schedule

    @staticmethod
    def update_schedule(
        *,
        schedule: Schedule,
        date_value: date,
        start_time_value: time,
        end_time_value: time,
        is_available: bool,
    ) -> Schedule:
        schedule.date = date_value
        schedule.start_time = start_time_value
        schedule.end_time = end_time_value
        schedule.is_available = is_available
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("This time slot already exists") from e
        return schedule

    @staticmethod
    def delete_schedule(schedule: Schedule) -> None:
        if schedule.appointment:
            raise ValueError("Cannot delete: this slot already has an appointment")
        db.session.delete(schedule)
        db.session.commit()

