import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.extensions import db
from app.services.chatbot_service import ChatbotService


def main():
    app = create_app()
    with app.app_context():
        uri = (app.config.get("SQLALCHEMY_DATABASE_URI") or "").lower()
        is_postgres = "postgresql" in uri
        rows = db.session.execute(
            db.text(
                """
                SELECT id, name, symptoms, description
                FROM diseases
                ORDER BY id ASC
                """
            )
        ).mappings().all()
        if not rows:
            print("No diseases found.")
            return

        updated = 0
        for r in rows:
            content = f"{r['name']}\nSymptoms: {r['symptoms']}\nDescription: {r['description']}"
            embedding = ChatbotService.embed_text(content)
            if is_postgres:
                vector_text = ChatbotService._vector_literal(embedding)
                db.session.execute(
                    db.text(
                        """
                        UPDATE diseases
                        SET embedding = CAST(:embedding AS vector)
                        WHERE id = :disease_id
                        """
                    ),
                    {"embedding": vector_text, "disease_id": int(r["id"])},
                )
            else:
                db.session.execute(
                    db.text(
                        """
                        UPDATE diseases
                        SET embedding = :embedding
                        WHERE id = :disease_id
                        """
                    ),
                    {"embedding": json.dumps(embedding), "disease_id": int(r["id"])},
                )
            updated += 1

        db.session.commit()
        print(f"Embedding generation completed. Updated {updated} diseases.")


if __name__ == "__main__":
    main()
