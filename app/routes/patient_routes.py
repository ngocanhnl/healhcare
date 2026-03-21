from datetime import date, timedelta

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.enums import AppointmentStatus, PaymentStatus, UserRole
from app.models.payment_transaction import PaymentTransaction
from app.models.schedule import Schedule
from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorService
from app.services.vnpay_service import VnpayService
from app.services.forms import BookingForm, NewAppointmentForm, SearchDoctorForm
from app.services.authz import roles_required

patient_bp = Blueprint("patient", __name__)


@patient_bp.get("/")
def home():
    return redirect(url_for("patient.search"))


@patient_bp.get("/doctors/search")
@patient_bp.post("/doctors/search")
def search():
    form = SearchDoctorForm()
    doctor_name = request.args.get("doctor_name") if request.method == "GET" else form.doctor_name.data
    hospital_name = request.args.get("hospital_name") if request.method == "GET" else form.hospital_name.data
    specialty = request.args.get("specialty") if request.method == "GET" else form.specialty.data
    min_exp = (
        request.args.get("min_experience_years", type=int)
        if request.method == "GET"
        else form.min_experience_years.data
    )
    max_exp = (
        request.args.get("max_experience_years", type=int)
        if request.method == "GET"
        else form.max_experience_years.data
    )

    if request.method == "POST" and form.validate_on_submit():
        params: dict[str, str | int] = {}
        doctor_name_value = (form.doctor_name.data or "").strip()
        if doctor_name_value:
            params["doctor_name"] = doctor_name_value
        hospital_name_value = (form.hospital_name.data or "").strip()
        if hospital_name_value:
            params["hospital_name"] = hospital_name_value
        specialty_value = (form.specialty.data or "").strip()
        if specialty_value:
            params["specialty"] = specialty_value
        if form.min_experience_years.data is not None:
            params["min_experience_years"] = int(form.min_experience_years.data)
        if form.max_experience_years.data is not None:
            params["max_experience_years"] = int(form.max_experience_years.data)
        return redirect(url_for("patient.search", **params))

    if request.method == "GET":
        form.doctor_name.data = (doctor_name or "").strip()
        form.hospital_name.data = (hospital_name or "").strip()
        form.specialty.data = (specialty or "").strip()
        form.min_experience_years.data = min_exp
        form.max_experience_years.data = max_exp

    doctors = DoctorService.search_doctors(
        doctor_name=doctor_name,
        hospital_name=hospital_name,
        specialty=specialty,
        min_experience_years=min_exp,
        max_experience_years=max_exp,
    )
    specialties = DoctorService.list_specialties()
    hospitals = DoctorService.list_hospitals()
    doctor_names = DoctorService.list_doctor_names()
    return render_template(
        "patient/search_doctor.html",
        form=form,
        doctors=doctors,
        specialties=specialties,
        hospitals=hospitals,
        doctor_names=doctor_names,
        selected_specialty=(specialty or "").strip(),
    )


@patient_bp.get("/doctors/<int:doctor_id>")
def doctor_detail(doctor_id: int):
    doctor = DoctorService.get_doctor(doctor_id)
    if not doctor:
        abort(404)
    schedules = DoctorService.get_available_schedules(doctor_id=doctor_id, from_date=date.today())
    return render_template("patient/doctor_detail.html", doctor=doctor, schedules=schedules)


@patient_bp.get("/appointments/new")
@patient_bp.post("/appointments/new")
@login_required
@roles_required(UserRole.PATIENT)
def appointment_new():
    form = NewAppointmentForm()

    hospital_id = request.args.get("hospital_id", type=int) if request.method == "GET" else None
    doctor_id = request.args.get("doctor_id", type=int) if request.method == "GET" else None
    date_value = request.args.get("date", type=str) if request.method == "GET" else None

    hospitals = DoctorService.list_hospital_options()
    form.hospital_id.choices = [("", "All hospitals")] + [(str(h_id), h_name) for h_id, h_name in hospitals]
    doctor_options = DoctorService.list_doctor_options(hospital_id=hospital_id)
    form.doctor_id.choices = [("", "Select doctor")] + [(str(d_id), d_name) for d_id, d_name in doctor_options]

    if request.method == "POST" and form.validate_on_submit():
        params: dict[str, str] = {}
        if form.hospital_id.data:
            params["hospital_id"] = str(form.hospital_id.data)
        if form.doctor_id.data:
            params["doctor_id"] = str(form.doctor_id.data)
        if form.date.data:
            params["date"] = form.date.data.isoformat()
        return redirect(url_for("patient.appointment_new", **params))

    if request.method == "GET":
        form.hospital_id.data = str(hospital_id) if hospital_id else ""
        form.doctor_id.data = str(doctor_id) if doctor_id else ""
        if date_value:
            try:
                form.date.data = date.fromisoformat(date_value)
            except ValueError:
                pass

    schedules = []
    schedules_by_date: dict[date, list] = {}
    selected_doctor = None
    if doctor_id:
        selected_doctor = DoctorService.get_doctor(doctor_id)
        if selected_doctor:
            if date_value:
                schedules = DoctorService.get_available_schedules(doctor_id=doctor_id, from_date=form.date.data)
                if form.date.data:
                    schedules = [s for s in schedules if s.date == form.date.data]
            else:
                end_date = date.today() + timedelta(days=6)
                schedules = DoctorService.get_available_schedules(doctor_id=doctor_id, from_date=date.today())
                schedules = [s for s in schedules if s.date <= end_date]
                for s in schedules:
                    schedules_by_date.setdefault(s.date, []).append(s)
                for d in schedules_by_date:
                    schedules_by_date[d].sort(key=lambda x: x.start_time)

    return render_template(
        "patient/new_appointment.html",
        form=form,
        schedules=schedules,
        schedules_by_date=schedules_by_date,
        selected_doctor=selected_doctor,
    )

@patient_bp.get("/book/<int:schedule_id>")
@patient_bp.post("/book/<int:schedule_id>")
@login_required
@roles_required(UserRole.PATIENT)
def book(schedule_id: int):
    form = BookingForm()
    amount = 500000.0  # Amount in VND (demo)
    schedule = Schedule.query.get(schedule_id)

    if schedule is None:
        abort(404)

    if form.validate_on_submit():
        ip_addr = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.remote_addr
            or "127.0.0.1"
        )

        txn_ref = VnpayService.generate_txn_ref()

        # VNPay order info: must be ASCII, no accents/special characters (demo).
        order_info = f"Thanh toan don hang {txn_ref}"

        transaction = PaymentTransaction(
            patient_id=current_user.id,
            schedule_id=schedule_id,
            vnp_txn_ref=txn_ref,
            amount_vnd=int(amount),
            status=PaymentStatus.PENDING,
        )
        db.session.add(transaction)
        db.session.commit()

        try:
            payment_url = VnpayService.create_payment_url(
                payment_url=current_app.config["VNPAY_PAYMENT_URL"],
                tmn_code=current_app.config["VNPAY_TMN_CODE"],
                hash_secret=current_app.config["VNPAY_HASH_SECRET"],
                return_url=url_for("patient.vnpay_return", _external=True),
                ip_addr=ip_addr,
                locale=current_app.config["VNPAY_LOCALE"],
                curr_code=current_app.config["VNPAY_CURR_CODE"],
                order_type=current_app.config["VNPAY_ORDER_TYPE"],
                txn_ref=txn_ref,
                amount_vnd=int(amount),
                order_info=order_info,
                version=current_app.config["VNPAY_VERSION"],
            )
        except Exception:
            transaction.status = PaymentStatus.FAILED
            db.session.commit()
            flash("Failed to create VNPay payment URL.", "danger")
            return render_template(
                "patient/booking.html",
                form=form,
                schedule_id=schedule_id,
                amount=amount,
                schedule=schedule,
            )

        return redirect(payment_url)

    return render_template(
        "patient/booking.html", form=form, schedule_id=schedule_id, amount=amount, schedule=schedule
    )


@patient_bp.get("/payment-result")
def vnpay_return():
    # VNPay callback: no CSRF needed, we validate VNPay signature.
    params = request.args.to_dict(flat=True)
    provided_secure_hash = params.get("vnp_SecureHash", "")
    vnp_txn_ref = params.get("vnp_TxnRef", "")
    response_code = params.get("vnp_ResponseCode", "")

    secure_valid = VnpayService.verify_return(
        hash_secret=current_app.config["VNPAY_HASH_SECRET"],
        vnp_params=params,
        provided_secure_hash=provided_secure_hash,
    )

    if not vnp_txn_ref:
        flash("Payment callback missing txn ref.", "danger")
        return redirect(url_for("auth.login"))

    transaction = db.session.execute(
        db.select(PaymentTransaction).where(PaymentTransaction.vnp_txn_ref == vnp_txn_ref)
    ).scalar_one_or_none()

    if not transaction:
        flash("Payment transaction not found.", "danger")
        return redirect(url_for("auth.login"))

    if transaction.status == PaymentStatus.SUCCESS:
        flash("Payment already processed.", "info")
        return redirect(url_for("patient.dashboard"))

    if secure_valid and response_code == "00":
        try:
            AppointmentService.book(
                patient_id=transaction.patient_id,
                schedule_id=transaction.schedule_id,
                status=AppointmentStatus.PENDING,
            )
            transaction.status = PaymentStatus.SUCCESS
            db.session.commit()
        except ValueError:
            transaction.status = PaymentStatus.FAILED
            db.session.commit()
            flash("Payment received but slot is no longer available.", "danger")
            return redirect(url_for("patient.dashboard"))

        flash("Payment successful. Appointment created (PENDING).", "success")
        return redirect(url_for("patient.dashboard"))

    transaction.status = PaymentStatus.FAILED
    db.session.commit()
    flash("Payment failed or invalid signature.", "danger")
    return redirect(url_for("patient.dashboard"))


@patient_bp.get("/patient/dashboard")
@login_required
@roles_required(UserRole.PATIENT)
def dashboard():
    appts = AppointmentService.list_for_patient(patient_id=current_user.id)
    return render_template("patient/dashboard.html", appointments=appts)

