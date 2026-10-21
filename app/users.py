import os

from flask import current_app
from flask_login import UserMixin
from sqlalchemy import select

from app.extensions import db
from app.models import User
from app.passwords import hash_password, verify_password


class StaffUser(UserMixin):
    def __init__(self, user: User):
        self.id = str(user.id)
        self.email = user.email
        self.nombre = user.nombre


def ensure_demo_user() -> None:
    email = os.environ.get("DEMO_USER", "permanencia@uniminuto.local").strip().lower()
    password = os.environ.get("DEMO_PASSWORD", "")
    if not password:
        current_app.logger.warning("DEMO_PASSWORD no está definida; no hay usuario de demostración.")
        return
    user = db.session.scalar(select(User).where(User.email == email))
    if user is None:
        db.session.add(
            User(
                email=email,
                nombre="Permanencia estudiantil",
                password_hash=hash_password(password),
            )
        )
        db.session.commit()
        current_app.logger.info("usuario de demostración listo")
        return
    if not verify_password(password, user.password_hash):
        user.password_hash = hash_password(password)
        db.session.commit()
    current_app.logger.info("usuario de demostración listo")
