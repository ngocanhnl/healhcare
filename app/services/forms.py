from datetime import date, time

from flask_wtf import FlaskForm
from wtforms import (
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields import DateField, IntegerField, TimeField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange, ValidationError

from app.extensions import db
from app.models.user import User
from app.models.enums import UserRole


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
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
    specialty = StringField("Specialty")
    description = TextAreaField("Description")
    experience_years = IntegerField("Experience (years)", default=0)

    submit = SubmitField("Create account")

    def validate_username(self, field):
        exists = db.session.execute(db.select(User.id).where(User.username == field.data)).scalar_one_or_none()
        if exists is not None:
            raise ValidationError("Username already exists")

    def validate_experience_years(self, field):
        if field.data is None:
            return
        if field.data < 0 or field.data > 80:
            raise ValidationError("Experience years must be between 0 and 80")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SearchDoctorForm(FlaskForm):
    specialty = StringField("Specialty", validators=[Length(max=120)])
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


class BookingForm(FlaskForm):
    submit = SubmitField("Book this slot")


class UpdateAppointmentStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[("CONFIRMED", "CONFIRMED"), ("CANCELLED", "CANCELLED")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update")

