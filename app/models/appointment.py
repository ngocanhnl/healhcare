from datetime import datetime

from app.extensions import db

from .enums import AppointmentStatus


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False, index=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedules.id"), nullable=False, unique=True)

    status = db.Column(db.Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.PENDING, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    patient = db.relationship("User", back_populates="patient_appointments", foreign_keys=[patient_id])
    doctor = db.relationship("Doctor", back_populates="appointments", foreign_keys=[doctor_id])
    schedule = db.relationship("Schedule", back_populates="appointment", foreign_keys=[schedule_id])

