from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models.doctor import Doctor
from app.models.hospital import Hospital
from app.models.enums import UserRole
from app.models.payment_transaction import PaymentTransaction
from app.models.schedule import Schedule
from app.models.user import User
from app.services.authz import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@login_required
@roles_required(UserRole.ADMIN)
def dashboard():
    username = (request.args.get("username") or "").strip()
    doctor_name = (request.args.get("doctor_name") or "").strip()
    patient_name = (request.args.get("patient_name") or "").strip()
    role_value = (request.args.get("role") or "").strip().upper()
    hospital_name = (request.args.get("hospital_name") or "").strip()
    specialty = (request.args.get("specialty") or "").strip()

    stmt = db.select(User).outerjoin(Doctor, Doctor.user_id == User.id).outerjoin(Hospital, Hospital.id == Doctor.hospital_id)

    if username:
        stmt = stmt.where(User.username.ilike(f"%{username}%"))
    if doctor_name:
        stmt = stmt.where(User.role == UserRole.DOCTOR, User.username.ilike(f"%{doctor_name}%"))
    if patient_name:
        stmt = stmt.where(User.role == UserRole.PATIENT, User.username.ilike(f"%{patient_name}%"))
    if role_value in {UserRole.ADMIN.value, UserRole.DOCTOR.value, UserRole.PATIENT.value}:
        stmt = stmt.where(User.role == UserRole(role_value))
    if hospital_name:
        stmt = stmt.where(User.role == UserRole.DOCTOR, Hospital.name.ilike(f"%{hospital_name}%"))
    if specialty:
        stmt = stmt.where(User.role == UserRole.DOCTOR, Doctor.specialty.ilike(f"%{specialty}%"))

    users = list(db.session.execute(stmt.order_by(User.id.desc())).scalars().all())
    filters = {
        "username": username,
        "doctor_name": doctor_name,
        "patient_name": patient_name,
        "role": role_value,
        "hospital_name": hospital_name,
        "specialty": specialty,
    }
    return render_template("admin/dashboard.html", users=users, filters=filters)


@admin_bp.post("/users/<int:user_id>/delete")
@login_required
@roles_required(UserRole.ADMIN)
def delete_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.dashboard"))
    if user.role == UserRole.ADMIN:
        flash("Cannot delete ADMIN account.", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        # Clean payment transactions by patient ownership.
        db.session.execute(db.delete(PaymentTransaction).where(PaymentTransaction.patient_id == user.id))

        # If deleting a doctor-account user, delete doctor profile first.
        # This avoids ORM trying to set doctors.user_id = NULL (NOT NULL column).
        doctor = db.session.execute(db.select(Doctor).where(Doctor.user_id == user.id)).scalar_one_or_none()
        if doctor:
            doctor_schedule_ids = db.session.execute(
                db.select(Schedule.id).where(Schedule.doctor_id == doctor.id)
            ).scalars().all()
            if doctor_schedule_ids:
                db.session.execute(
                    db.delete(PaymentTransaction).where(PaymentTransaction.schedule_id.in_(doctor_schedule_ids))
                )
            db.session.delete(doctor)

        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Delete failed. Data constraints prevented this action.", "danger")
        return redirect(url_for("admin.dashboard"))

    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.dashboard"))

