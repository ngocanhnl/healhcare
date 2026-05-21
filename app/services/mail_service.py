from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import TYPE_CHECKING

from flask import current_app, has_app_context

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.enums import AppointmentStatus

logger = logging.getLogger(__name__)

_STATUS_VI: dict[str, str] = {
    "PENDING": "Cho xac nhan",
    "CONFIRMED": "Da xac nhan",
    "CANCELLED": "Da huy",
}


def _enum_value(status: AppointmentStatus | str) -> str:
    return status.value if hasattr(status, "value") else str(status)


def _status_label_vi(status: AppointmentStatus | str) -> str:
    key = _enum_value(status)
    return _STATUS_VI.get(key, key)


def _resolve_recipient_email(appointment: Appointment) -> str | None:
    raw = (getattr(appointment, "contact_email", None) or "").strip()
    if raw:
        return raw
    patient = getattr(appointment, "patient", None)
    if patient:
        return (getattr(patient, "email", None) or "").strip() or None
    return None


def _doctor_display_name(appointment: Appointment) -> str:
    doctor = getattr(appointment, "doctor", None)
    if not doctor:
        return "Bac si"
    user = getattr(doctor, "user", None)
    if user:
        return user.display_name
    return f"Bac si #{doctor.id}"


def _slot_description(appointment: Appointment) -> str:
    schedule = getattr(appointment, "schedule", None)
    if not schedule:
        return "(chua co thong tin lich)"
    d = schedule.date.strftime("%d/%m/%Y")
    st = schedule.start_time.strftime("%H:%M")
    et = schedule.end_time.strftime("%H:%M")
    return f"{d} {st} - {et}"


def notify_patient_appointment_status_changed(
    *,
    appointment: Appointment,
    previous_status: AppointmentStatus,
) -> None:
    """Gui email cho benh nhan khi trang thai lich hen thay doi (neu cau hinh SMTP hop le)."""
    if not has_app_context():
        return
    if previous_status == appointment.status:
        return

    cfg = current_app.config
    server = (cfg.get("MAIL_SERVER") or "").strip()
    if not server:
        logger.debug("MAIL_SERVER khong cau hinh — bo qua gui email lich hen id=%s", appointment.id)
        return
    if cfg.get("MAIL_SUPPRESS_SEND"):
        logger.info(
            "MAIL_SUPPRESS_SEND: bo qua gui email (lich hen id=%s, to=%s)",
            appointment.id,
            _resolve_recipient_email(appointment),
        )
        return

    to_addr = _resolve_recipient_email(appointment)
    if not to_addr:
        logger.info("Khong co email lien he — bo qua thong bao lich hen id=%s", appointment.id)
        return

    sender = cfg.get("MAIL_DEFAULT_SENDER") or cfg.get("MAIL_USERNAME")
    if not sender:
        logger.warning("MAIL_DEFAULT_SENDER / MAIL_USERNAME chua cau hinh — khong gui duoc email.")
        return

    patient_name = (getattr(appointment, "contact_fullname", None) or "Quy khach").strip()
    doctor_name = _doctor_display_name(appointment)
    slot = _slot_description(appointment)
    old_l = _status_label_vi(previous_status)
    new_l = _status_label_vi(appointment.status)

    subject = f"[Lich kham] Trang thai lich hen da cap nhat — {new_l}"
    body = (
        f"Xin chao {patient_name},\n\n"
        f"Lich kham cua ban voi bac si {doctor_name} ({slot}) da duoc cap nhat.\n"
        f"- Trang thai truoc: {old_l}\n"
        f"- Trang thai moi: {new_l}\n\n"
        f"Ma lich hen: #{appointment.id}\n\n"
        "Tran trong,\n"
        "He thong dat lich kham\n"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_addr
    msg.set_content(body)

    port = int(cfg.get("MAIL_PORT") or 587)
    use_tls = bool(cfg.get("MAIL_USE_TLS"))
    use_ssl = bool(cfg.get("MAIL_USE_SSL"))
    username = (cfg.get("MAIL_USERNAME") or "").strip() or None
    password = cfg.get("MAIL_PASSWORD") or None

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(server, port, timeout=30) as smtp:
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(server, port, timeout=30) as smtp:
                if use_tls:
                    smtp.starttls()
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)
        logger.info("Da gui email cap nhat trang thai lich hen id=%s toi %s", appointment.id, to_addr)
    except (OSError, smtplib.SMTPException) as e:
        logger.warning("Gui email lich hen id=%s that bai: %s", appointment.id, e)
