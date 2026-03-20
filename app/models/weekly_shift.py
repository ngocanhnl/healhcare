from app.extensions import db


class WeeklyShift(db.Model):
    __tablename__ = "weekly_shifts"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False, index=True)

    # Monday=0 ... Sunday=6 (datetime.date.weekday)
    weekday = db.Column(db.Integer, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    doctor = db.relationship("Doctor", back_populates="weekly_shifts")

    __table_args__ = (
        db.UniqueConstraint("doctor_id", "weekday", "start_time", "end_time", name="uq_weekly_shift"),
    )

