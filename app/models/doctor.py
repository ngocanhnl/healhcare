from app.extensions import db


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    specialty = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    experience_years = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship("User", back_populates="doctor_profile")
    schedules = db.relationship(
        "Schedule", back_populates="doctor", cascade="all, delete-orphan", order_by="Schedule.date,Schedule.start_time"
    )
    appointments = db.relationship(
        "Appointment", back_populates="doctor", cascade="all, delete-orphan"
    )

