import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.extensions import db


SAMPLE_DISEASES = [
    {
        "name": "Viem hong cap",
        "symptoms": "dau hong, sot nhe, ho kho, met moi",
        "description": "Tinh trang viem niem mac hong thuong do virus hoac vi khuan.",
        "specialty": "ENT",
    },
    {
        "name": "Dai trang kich thich",
        "symptoms": "dau bung, roi loan tieu hoa, tieu chay hoac tao bon",
        "description": "Roi loan chuc nang duong ruot, can danh gia boi chuyen khoa tieu hoa.",
        "specialty": "Gastroenterology",
    },
    {
        "name": "Tang huyet ap",
        "symptoms": "dau dau, choang vang, hoi hop, co the khong co trieu chung",
        "description": "Benh ly man tinh lien quan den huyet ap cao, can theo doi dai han.",
        "specialty": "Cardiology",
    },
]


def main():
    app = create_app()
    with app.app_context():
        for d in SAMPLE_DISEASES:
            exists = db.session.execute(
                db.text("SELECT id FROM diseases WHERE name = :name LIMIT 1"),
                {"name": d["name"]},
            ).first()
            if exists:
                continue
            db.session.execute(
                db.text(
                    """
                    INSERT INTO diseases (name, symptoms, description, specialty)
                    VALUES (:name, :symptoms, :description, :specialty)
                    """
                ),
                d,
            )
        db.session.commit()
        print("Seed diseases completed.")


if __name__ == "__main__":
    main()
