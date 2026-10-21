import os

from flask import Flask, flash, redirect, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import ROOT, build_config, load_local_env
from app.extensions import csrf, db, login_manager

_CSP = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net; "
    "style-src 'self' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


def create_app() -> Flask:
    load_local_env()
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    app.config.update(build_config())

    if os.environ.get("RENDER") == "true":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User
    from app.users import StaffUser, ensure_demo_user

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            key = int(user_id)
        except (TypeError, ValueError):
            return None
        user = db.session.get(User, key)
        if user is None:
            return None
        return StaffUser(user)

    from app.routes import bp

    app.register_blueprint(bp)

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = _CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        if current_user.is_authenticated:
            flash("El archivo supera el tamaño máximo de 2 MB.", "import_error")
            return redirect(url_for("main.panel"))
        return redirect(url_for("main.login"))

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        flash("La sesión del formulario expiró. Vuelve a intentar.", "error")
        target = "main.panel" if current_user.is_authenticated else "main.login"
        return redirect(url_for(target))

    @app.template_filter("nota")
    def nota(value):
        return f"{float(value):.2f}".replace(".", ",")

    with app.app_context():
        db.create_all()
        ensure_demo_user()

    return app
