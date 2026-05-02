from datetime import date, time, timedelta

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.schedule import Schedule
from app.models.weekly_shift import WeeklyShift


class ScheduleService:
    @staticmethod
    def list_doctor_schedules(*, doctor_id: int) -> list[Schedule]:
        stmt = db.select(Schedule).where(Schedule.doctor_id == doctor_id).order_by(
            Schedule.date.desc(), Schedule.start_time.desc()
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def create_schedule(
        *,
        doctor_id: int,
        date_value: date,
        start_time_value: time,
        end_time_value: time,
        is_available: bool,
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
    def ensure_week_schedules_from_templates(*, doctor_id: int, week_start: date) -> int:
        week_end = week_start + timedelta(days=6)
        shifts = list(
            db.session.execute(
                db.select(WeeklyShift)
                .where(
                    WeeklyShift.doctor_id == doctor_id,
                    WeeklyShift.week_start == week_start,
                    WeeklyShift.is_active.is_(True),
                )
                .order_by(WeeklyShift.weekday, WeeklyShift.start_time)
            ).scalars().all()
        )
        if not shifts:
            return 0

        created = 0
        existing_rows = db.session.execute(
            db.select(Schedule.date, Schedule.start_time, Schedule.end_time).where(
                Schedule.doctor_id == doctor_id,
                Schedule.date >= week_start,
                Schedule.date <= week_end,
            )
        ).all()
        existing = {(r[0], r[1], r[2]) for r in existing_rows}

        for sh in shifts:
            d = week_start + timedelta(days=sh.weekday)
            key = (d, sh.start_time, sh.end_time)
            if key in existing:
                continue
            db.session.add(
                Schedule(
                    doctor_id=doctor_id,
                    date=d,
                    start_time=sh.start_time,
                    end_time=sh.end_time,
                    is_available=True,
                )
            )
            created += 1
            existing.add(key)

        if created:
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
        return created

    @staticmethod
    def delete_week_template_and_schedule(*, shift: WeeklyShift) -> tuple[bool, str | None]:
        schedule_date = shift.week_start + timedelta(days=shift.weekday)
        schedule = db.session.execute(
            db.select(Schedule).where(
                Schedule.doctor_id == shift.doctor_id,
                Schedule.date == schedule_date,
                Schedule.start_time == shift.start_time,
                Schedule.end_time == shift.end_time,
            )
        ).scalar_one_or_none()

        kept_booked_schedule = False
        if schedule:
            if schedule.appointment:
                kept_booked_schedule = True
            else:
                db.session.delete(schedule)

        db.session.delete(shift)
        db.session.commit()

        if kept_booked_schedule:
            return True, "Weekly template deleted, but the booked slot in this week was kept."
        return False, None

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

