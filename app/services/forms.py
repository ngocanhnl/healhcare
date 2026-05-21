from datetime import date, time

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields import DateField, IntegerField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError

from app.extensions import db
from app.models.user import User
from app.models.enums import UserRole
from app.models.hospital import Hospital
from app.models.medical_specialties import (
    is_valid_medical_specialty,
    specialty_form_choices,
    specialty_search_choices,
)


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    full_name = StringField("Họ và tên", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[DataRequired(), Length(min=8, max=20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=72)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords do not match")],
    )
    role = SelectField(
        "Role",
        choices=[(UserRole.PATIENT.value, "Patient"), (UserRole.DOCTOR.value, "Doctor")],
        validators=[DataRequired()],
    )

    # Doctor extra fields (only used when role=DOCTOR)
    specialty = SelectField("Chuyên khoa", choices=specialty_form_choices(), validators=[Optional()])
    hospital_id = SelectField("Hospital/Clinic", choices=[(0, "-- Select hospital --")], coerce=int)
    description = TextAreaField("Description")
    experience_years = IntegerField("Experience (years)", default=0)

    submit = SubmitField("Create account")

    def validate_username(self, field):
        exists = db.session.execute(db.select(User.id).where(User.username == field.data)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Username already exists")

    def validate_email(self, field):
        email_value = (field.data or "").strip()
        exists = db.session.execute(db.select(User.id).where(User.email == email_value)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Email already exists")

    def validate_phone(self, field):
        phone_value = (field.data or "").strip()
        exists = db.session.execute(db.select(User.id).where(User.phone == phone_value)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Phone already exists")

    def validate_experience_years(self, field):
        if field.data is None:
            return
        if field.data < 0 or field.data > 80:
            raise ValidationError("Experience years must be between 0 and 80")

    def validate_specialty(self, field):
        if self.role.data != UserRole.DOCTOR.value:
            return
        if not (field.data or "").strip():
            raise ValidationError("Vui lòng chọn chuyên khoa cho tài khoản bác sĩ")
        if not is_valid_medical_specialty(field.data):
            raise ValidationError("Chuyên khoa không hợp lệ")

    def validate_hospital_id(self, field):
        if self.role.data != UserRole.DOCTOR.value:
            return
        if not field.data:
            raise ValidationError("Please select a hospital for DOCTOR account")
        exists = db.session.execute(db.select(Hospital.id).where(Hospital.id == field.data)).scalar_one_or_none()
        if exists is None:
            raise ValidationError("Selected hospital does not exist")

    def set_hospital_choices(self):
        hospitals = list(db.session.execute(db.select(Hospital).order_by(Hospital.name.asc())).scalars().all())
        self.hospital_id.choices = [(0, "-- Select hospital --")] + [(h.id, h.name) for h in hospitals]


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SearchDoctorForm(FlaskForm):
    doctor_name = StringField("Họ tên bác sĩ", validators=[Optional(), Length(max=120)])
    hospital_name = StringField("Hospital/Clinic", validators=[Optional(), Length(max=160)])
    specialty = SelectField("Chuyên khoa", choices=specialty_search_choices(), validators=[Optional()])
    submit = SubmitField("Search")


class ScheduleForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()], default=date.today)
    start_time = TimeField("Start time", validators=[DataRequired()], default=time(9, 0))
    end_time = TimeField("End time", validators=[DataRequired()], default=time(10, 0))
    is_available = SelectField(
        "Availability",
        choices=[("1", "Available"), ("0", "Busy")],
        validators=[DataRequired()],
        default="1",
    )
    submit = SubmitField("Save")

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError("End time must be after start time")


class WeeklyShiftForm(FlaskForm):
    weekday = SelectField(
        "Day of week",
        choices=[
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        validators=[DataRequired()],
    )
    start_time = TimeField("Start time", validators=[DataRequired()], default=time(7, 0))
    end_time = TimeField("End time", validators=[DataRequired()], default=time(8, 0))
    submit = SubmitField("Add shift")

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError("End time must be after start time")


class BookingForm(FlaskForm):
    booking_for = SelectField(
        "Booking for",
        choices=[("self", "Myself"), ("relative", "Relative")],
        validators=[DataRequired()],
        default="self",
    )
    fullname = StringField("Full name", validators=[Optional(), Length(min=2, max=80)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(min=8, max=20)])
    symptoms = TextAreaField("Symptoms", validators=[Optional(), Length(max=2000)])
    agreed = BooleanField("I confirm the payment", validators=[DataRequired()])
    submit = SubmitField("Pay with VNPay")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if not (self.symptoms.data or "").strip():
            self.symptoms.errors.append("Symptoms are required.")
            return False
        if self.booking_for.data == "relative":
            if not (self.fullname.data or "").strip():
                self.fullname.errors.append("Full name is required when booking for a relative.")
                return False
            if not (self.email.data or "").strip():
                self.email.errors.append("Email is required when booking for a relative.")
                return False
            if not (self.phone.data or "").strip():
                self.phone.errors.append("Phone is required when booking for a relative.")
                return False
            if not (self.symptoms.data or "").strip():
                self.symptoms.errors.append("Symptoms are required when booking for a relative.")
                return False
        return True


class PatientContactForm(FlaskForm):
    full_name = StringField("Họ và tên", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(min=8, max=20)])
    submit = SubmitField("Update contact info")


class DoctorReviewForm(FlaskForm):
    stars = IntegerField("Sao (1-5)", validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField("Bình luận", validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField("Gửi đánh giá")


class NewAppointmentForm(FlaskForm):
    hospital_id = SelectField("Hospital/Clinic", choices=[], default="", validate_choice=False)
    doctor_id = SelectField("Doctor", choices=[], default="", validate_choice=False)
    date = DateField("Date", default=date.today)
    submit = SubmitField("Search slots")


class UpdateAppointmentStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[("CONFIRMED", "CONFIRMED"), ("CANCELLED", "CANCELLED")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update")


class DoctorProfileForm(FlaskForm):
    full_name = StringField("Họ và tên", validators=[DataRequired(), Length(min=2, max=120)])
    specialty = SelectField("Chuyên khoa", choices=specialty_form_choices(), validators=[DataRequired()])
    hospital_name = StringField("Hospital/Clinic", validators=[Length(max=160)])
    description = TextAreaField("Description", validators=[Length(max=2000)])
    experience_years = IntegerField("Experience (years)", validators=[DataRequired(), NumberRange(min=0, max=80)])
    price_vnd = IntegerField(
        "Giá đặt lịch (VND)",
        validators=[DataRequired(), NumberRange(min=1, max=1000000000)],
        default=500000,
    )
    submit = SubmitField("Save profile")


class DiseaseAdminForm(FlaskForm):
    name = StringField("Disease name", validators=[DataRequired(), Length(min=2, max=255)])
    symptoms = TextAreaField("Symptoms", validators=[DataRequired(), Length(min=3, max=8000)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=3, max=8000)])
    specialty = StringField("Specialty", validators=[DataRequired(), Length(min=2, max=120)])
    submit = SubmitField("Save disease")


class HospitalAdminForm(FlaskForm):
    name = StringField("Hospital name", validators=[DataRequired(), Length(min=2, max=160)])
    submit = SubmitField("Create hospital")


class AdminCreatePatientForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(min=3, max=80)])
    full_name = StringField("Họ và tên", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Số điện thoại", validators=[DataRequired(), Length(min=8, max=20)])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=6, max=72)])
    confirm_password = PasswordField(
        "Nhập lại mật khẩu",
        validators=[DataRequired(), EqualTo("password", message="Mật khẩu không khớp")],
    )
    submit = SubmitField("Tạo bệnh nhân")

    def validate_username(self, field):
        exists = db.session.execute(db.select(User.id).where(User.username == field.data)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Tên đăng nhập đã tồn tại")

    def validate_email(self, field):
        email_value = (field.data or "").strip()
        exists = db.session.execute(db.select(User.id).where(User.email == email_value)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Email đã được dùng")

    def validate_phone(self, field):
        phone_value = (field.data or "").strip()
        exists = db.session.execute(db.select(User.id).where(User.phone == phone_value)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Số điện thoại đã được dùng")


class AdminCreateDoctorForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(min=3, max=80)])
    full_name = StringField("Họ và tên", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Số điện thoại", validators=[DataRequired(), Length(min=8, max=20)])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=6, max=72)])
    confirm_password = PasswordField(
        "Nhập lại mật khẩu",
        validators=[DataRequired(), EqualTo("password", message="Mật khẩu không khớp")],
    )
    specialty = SelectField("Chuyên khoa", choices=specialty_form_choices(), validators=[DataRequired()])
    hospital_id = SelectField("Bệnh viện / phòng khám", choices=[(0, "-- Chọn cơ sở --")], coerce=int)
    description = TextAreaField("Giới thiệu", validators=[Optional(), Length(max=2000)])
    experience_years = IntegerField("Số năm kinh nghiệm", validators=[Optional(), NumberRange(min=0, max=80)], default=0)
    price_vnd = IntegerField(
        "Giá đặt lịch (VND)",
        validators=[DataRequired(), NumberRange(min=1, max=1000000000)],
        default=500000,
    )
    submit = SubmitField("Tạo bác sĩ")

    def validate_username(self, field):
        exists = db.session.execute(db.select(User.id).where(User.username == field.data)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Tên đăng nhập đã tồn tại")

    def validate_email(self, field):
        email_value = (field.data or "").strip()
        exists = db.session.execute(db.select(User.id).where(User.email == email_value)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Email đã được dùng")

    def validate_phone(self, field):
        phone_value = (field.data or "").strip()
        exists = db.session.execute(db.select(User.id).where(User.phone == phone_value)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Số điện thoại đã được dùng")

    def validate_hospital_id(self, field):
        if not field.data:
            raise ValidationError("Vui lòng chọn bệnh viện / phòng khám")
        exists = db.session.execute(db.select(Hospital.id).where(Hospital.id == field.data)).scalar_one_or_none()
        if exists is None:
            raise ValidationError("Cơ sở đã chọn không tồn tại")

    def validate_experience_years(self, field):
        if field.data is None:
            return
        if field.data < 0 or field.data > 80:
            raise ValidationError("Kinh nghiệm phải từ 0 đến 80 năm")

    def set_hospital_choices(self):
        hospitals = list(db.session.execute(db.select(Hospital).order_by(Hospital.name.asc())).scalars().all())
        self.hospital_id.choices = [(0, "-- Chọn cơ sở --")] + [(h.id, h.name) for h in hospitals]

