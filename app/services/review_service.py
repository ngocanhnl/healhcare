from sqlalchemy import func

from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor_review import DoctorReview
from app.models.enums import PaymentStatus
from app.models.payment_transaction import PaymentTransaction


class DoctorReviewService:
    @staticmethod
    def get_review_by_appointment_id(*, appointment_id: int) -> DoctorReview | None:
        return db.session.execute(
            db.select(DoctorReview).where(DoctorReview.appointment_id == appointment_id)
        ).scalar_one_or_none()

    @staticmethod
    def _is_paid_for_appointment(*, patient_id: int, appointment: Appointment) -> bool:
        exists = db.session.execute(
            db.select(PaymentTransaction.id)
            .where(
                PaymentTransaction.patient_id == patient_id,
                PaymentTransaction.schedule_id == appointment.schedule_id,
                PaymentTransaction.status == PaymentStatus.SUCCESS,
            )
            .limit(1)
        ).scalar_one_or_none()
        return exists is not None

    @staticmethod
    def create_review(*, appointment_id: int, patient_id: int, stars: int, comment: str) -> DoctorReview:
        appointment = db.session.get(Appointment, appointment_id)
        if not appointment:
            raise ValueError("Không tìm thấy lịch hẹn")

        if appointment.patient_id != patient_id:
            raise PermissionError("Bạn không có quyền đánh giá lịch hẹn này")

        if appointment.status.value == "CANCELLED":
            raise ValueError("Không thể đánh giá lịch hẹn đã hủy")

        if not DoctorReviewService._is_paid_for_appointment(patient_id=patient_id, appointment=appointment):
            raise ValueError("Bạn cần thanh toán thành công trước khi đánh giá")

        existing = DoctorReviewService.get_review_by_appointment_id(appointment_id=appointment_id)
        if existing:
            raise ValueError("Lịch hẹn này đã được đánh giá")

        if not (1 <= int(stars) <= 5):
            raise ValueError("Số sao phải nằm trong khoảng 1 đến 5")

        review = DoctorReview(
            appointment_id=appointment_id,
            doctor_id=appointment.doctor_id,
            patient_id=patient_id,
            stars=int(stars),
            comment=(comment or "").strip(),
        )
        if not review.comment:
            raise ValueError("Bình luận là bắt buộc")

        db.session.add(review)
        db.session.commit()
        return review

    @staticmethod
    def list_reviews_for_doctor(*, doctor_id: int, limit: int = 10) -> list[DoctorReview]:
        stmt = (
            db.select(DoctorReview)
            .where(DoctorReview.doctor_id == doctor_id)
            .order_by(DoctorReview.created_at.desc())
            .limit(limit)
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_rating_summary_for_doctor(*, doctor_id: int) -> tuple[float, int, int]:
        avg_value = db.session.execute(
            db.select(func.avg(DoctorReview.stars)).where(DoctorReview.doctor_id == doctor_id)
        ).scalar_one_or_none()

        count_value = db.session.execute(
            db.select(func.count(DoctorReview.id)).where(DoctorReview.doctor_id == doctor_id)
        ).scalar_one()

        avg_rating = float(avg_value or 0.0)
        avg_rating_rounded = int(round(avg_rating))

        return avg_rating, int(count_value or 0), avg_rating_rounded

