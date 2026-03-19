from flask import Blueprint, render_template
from flask_login import login_required

from app.extensions import db
from app.models.enums import UserRole
from app.models.user import User
from app.services.authz import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@login_required
@roles_required(UserRole.ADMIN)
def dashboard():
    users = list(db.session.execute(db.select(User).order_by(User.id.desc())).scalars().all())
    return render_template("admin/dashboard.html", users=users)

