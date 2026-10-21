from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from io import BytesIO
from sqlalchemy import select, text
from werkzeug.utils import secure_filename
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length

from app.excel_import import parse_xlsx
from app.extensions import db
from app.limiter import clear_failures, is_limited, record_failure
from app.models import ImportBatch, Student
from app.passwords import verify_dummy, verify_password
from app.persist import ImportPersistError, guardar_carga
from app.reports import BOGOTA, build_pdf
from app.risk import EN_RIESGO, NIVELES
from app.users import StaffUser

bp = Blueprint("main", __name__)
_SAMPLE = Path(__file__).resolve().parent.parent / "sample" / "estudiantes_ejemplo.xlsx"


class LoginForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Length(max=120)])
    password = PasswordField(validators=[DataRequired(), Length(max=200)])


@bp.get("/healthz")
def healthz():
    db.session.execute(text("SELECT 1"))
    return {"status": "ok"}


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.panel"))
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        password = form.password.data or ""
        ip = request.remote_addr or "desconocida"
        if is_limited(ip):
            error = "Demasiados intentos. Espera 15 minutos e inténtalo de nuevo."
            return render_template("login.html", form=form, error=error), 429
        user = _authenticate(email, password)
        if user is None:
            record_failure(ip)
            error = "Correo o contraseña incorrectos."
        else:
            clear_failures(ip)
            login_user(StaffUser(user))
            from flask import session

            session.permanent = True
            return redirect(url_for("main.panel"))
    elif request.method == "POST":
        error = "Escribe el correo y la contraseña."
    return render_template("login.html", form=form, error=error)


@bp.post("/salir")
@login_required
def salir():
    logout_user()
    return redirect(url_for("main.login"))


@bp.get("/")
@login_required
def panel():
    students = db.session.scalars(
        select(Student).order_by(Student.risk_score.desc(), Student.nombre.asc())
    ).all()
    en_riesgo = [student for student in students if student.risk_level in EN_RIESGO]
    sin_riesgo = [student for student in students if student.risk_level not in EN_RIESGO]
    by_level = {nivel: 0 for nivel in NIVELES}
    by_program: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "en_riesgo": 0})
    for student in students:
        by_level[student.risk_level] += 1
        bucket = by_program[student.programa]
        bucket["total"] += 1
        if student.risk_level in EN_RIESGO:
            bucket["en_riesgo"] += 1
    programas = [
        {"nombre": nombre, "en_riesgo": counts["en_riesgo"], "total": counts["total"]}
        for nombre, counts in sorted(by_program.items(), key=lambda item: (-item[1]["en_riesgo"], item[0]))
    ]
    last = db.session.scalar(select(ImportBatch).order_by(ImportBatch.created_at.desc()))
    return render_template(
        "panel.html",
        students=students,
        en_riesgo=en_riesgo,
        sin_riesgo=sin_riesgo,
        total=len(students),
        resumen_riesgo=_resumen(by_level),
        chart={
            "labels": list(NIVELES),
            "niveles": [by_level[nivel] for nivel in NIVELES],
            "programas": programas,
        },
        ultima_carga=_ultima_carga(last),
    )


@bp.post("/cargar")
@login_required
def cargar():
    upload = request.files.get("archivo")
    filename = (upload.filename or "") if upload is not None else ""
    if upload is None or filename.strip() == "":
        flash("Selecciona un archivo Excel.", "import_error")
        return redirect(url_for("main.panel"))
    if not filename.lower().endswith(".xlsx"):
        flash("Solo se acepta un archivo .xlsx, sin macros.", "import_error")
        return redirect(url_for("main.panel"))

    data = upload.read()
    rows, errors = parse_xlsx(data)
    if errors:
        for message in errors[:30]:
            flash(message, "import_error")
        if len(errors) > 30:
            flash(
                f"Hay {len(errors) - 30} errores más. Corrige el archivo y cárgalo de nuevo.",
                "import_error",
            )
        current_app.logger.info("carga_rechazada user_id=%s errores=%s", current_user.id, len(errors))
        return redirect(url_for("main.panel"))

    stored_name = secure_filename(filename)[:120] or "carga.xlsx"
    try:
        inserted, updated = guardar_carga(rows, int(current_user.id), stored_name)
    except ImportPersistError:
        current_app.logger.error("carga_fallida user_id=%s", current_user.id)
        flash("No se pudo guardar la carga. No se modificó ningún estudiante.", "import_error")
        return redirect(url_for("main.panel"))

    current_app.logger.info(
        "carga_ok user_id=%s filas=%s nuevos=%s actualizados=%s",
        current_user.id,
        len(rows),
        inserted,
        updated,
    )
    flash(
        f"Carga lista. {inserted} estudiantes nuevos y {updated} actualizados, sin duplicar documentos.",
        "ok",
    )
    return redirect(url_for("main.panel"))


@bp.get("/reporte.pdf")
@login_required
def reporte():
    students = db.session.scalars(select(Student)).all()
    payload = build_pdf(students)
    return send_file(
        BytesIO(payload),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="estudiantes_en_riesgo.pdf",
    )


@bp.get("/plantilla.xlsx")
@login_required
def plantilla():
    return send_file(
        _SAMPLE,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="estudiantes_ejemplo.xlsx",
    )


def _authenticate(email: str, password: str):
    from app.models import User

    user = db.session.scalar(select(User).where(User.email == email))
    if user is None:
        verify_dummy(password)
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def _resumen(by_level: dict[str, int]) -> str:
    return " · ".join(
        (
            _cuenta(by_level["Crítico"], "crítico", "críticos"),
            _cuenta(by_level["Alto"], "alto", "altos"),
            _cuenta(by_level["Medio"], "medio", "medios"),
        )
    )


def _cuenta(amount: int, singular: str, plural: str) -> str:
    return f"{amount} {singular if amount == 1 else plural}"


def _ultima_carga(batch: ImportBatch | None) -> str | None:
    if batch is None:
        return None
    moment = batch.created_at
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=ZoneInfo("UTC"))
    local = moment.astimezone(BOGOTA)
    return (
        f"{local:%d/%m/%Y %H:%M} · {batch.inserted_count} nuevos · {batch.updated_count} actualizados"
    )
