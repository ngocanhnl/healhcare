from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.enums import UserRole
from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorService
from app.services.forms import BookingForm, SearchDoctorForm
from app.services.authz import roles_required

patient_bp = Blueprint("patient", __name__)


@patient_bp.get("/")
def home():
    return redirect(url_for("patient.search"))


@patient_bp.get("/doctors/search")
@patient_bp.post("/doctors/search")
def search():
    form = SearchDoctorForm()
    specialty = request.args.get("specialty") if request.method == "GET" else form.specialty.data
    if request.method == "POST" and form.validate_on_submit():
        return redirect(url_for("patient.search", specialty=(form.specialty.data or "").strip()))

    doctors = DoctorService.search_doctors(specialty=specialty)
    specialties = DoctorService.list_specialties()
    return render_template(
        "patient/search_doctor.html",
        form=form,
        doctors=doctors,
        specialties=specialties,
        selected_specialty=(specialty or "").strip(),
    )


@patient_bp.get("/doctors/<int:doctor_id>")
def doctor_detail(doctor_id: int):
    doctor = DoctorService.get_doctor(doctor_id)
    if not doctor:
        abort(404)
    schedules = DoctorService.get_available_schedules(doctor_id=doctor_id, from_date=date.today())
    return render_template("patient/doctor_detail.html", doctor=doctor, schedules=schedules)


@patient_bp.get("/book/<int:schedule_id>")
@patient_bp.post("/book/<int:schedule_id>")
@login_required
@roles_required(UserRole.PATIENT)
def book(schedule_id: int):
    form = BookingForm()
    if form.validate_on_submit():
        try:
            AppointmentService.book(patient_id=current_user.id, schedule_id=schedule_id)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("patient.search"))
        flash("Appointment created (PENDING). Doctor will confirm.", "success")
        return redirect(url_for("patient.dashboard"))

    return render_template("patient/booking.html", form=form, schedule_id=schedule_id)


@patient_bp.get("/patient/dashboard")
@login_required
@roles_required(UserRole.PATIENT)
def dashboard():
    appts = AppointmentService.list_for_patient(patient_id=current_user.id)
    return render_template("patient/dashboard.html", appointments=appts)

