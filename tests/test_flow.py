import os
import re
from io import BytesIO

import pytest
from sqlalchemy import func, select, text

os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DEMO_USER"] = "permanencia@uniminuto.local"
os.environ["DEMO_PASSWORD"] = "clave-de-prueba-123"
os.environ["DATABASE_URL"] = "postgresql://antes:antes@localhost:55432/antes_test"
os.environ.pop("RENDER", None)

from app import create_app
from app.excel_import import parse_xlsx
from app.extensions import db
from app.limiter import reset
from app.models import Student
from tests.test_excel import valid_row, workbook_bytes

CSRF = re.compile(r'name="csrf_token"[^>]*value="([^"]+)"')


@pytest.fixture(scope="module")
def app():
    application = create_app()
    application.config["TESTING"] = True
    yield application


@pytest.fixture
def client(app):
    reset()
    with app.app_context():
        db.session.execute(text("TRUNCATE TABLE import_batches, students RESTART IDENTITY"))
        db.session.commit()
    return app.test_client()


def _token(html: str) -> str:
    match = CSRF.search(html)
    assert match, html[:400]
    return match.group(1)


def _login(client):
    page = client.get("/login")
    return client.post(
        "/login",
        data={
            "email": "permanencia@uniminuto.local",
            "password": "clave-de-prueba-123",
            "csrf_token": _token(page.get_data(as_text=True)),
        },
        follow_redirects=True,
    )


def _upload(client, payload, name="estudiantes.xlsx"):
    page = client.get("/")
    return client.post(
        "/cargar",
        data={"csrf_token": _token(page.get_data(as_text=True)), "archivo": (BytesIO(payload), name)},
        follow_redirects=True,
    )


def _count(app) -> int:
    with app.app_context():
        return db.session.scalar(select(func.count()).select_from(Student))


def test_salud_y_cabeceras(app):
    client = app.test_client()
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.get_json()["status"] == "ok"
    login = client.get("/login")
    assert "Content-Security-Policy" in login.headers
    assert "frame-ancestors 'none'" in login.headers["Content-Security-Policy"]
    assert login.headers["X-Frame-Options"] == "DENY"
    assert login.headers["X-Content-Type-Options"] == "nosniff"


def test_login_cookie_y_csrf(client):
    blocked = client.post(
        "/login",
        data={"email": "a@b.co", "password": "12345678"},
        follow_redirects=True,
    )
    assert "expiró" in blocked.get_data(as_text=True)

    page = client.post(
        "/login",
        data={
            "email": "permanencia@uniminuto.local",
            "password": "clave-de-prueba-123",
            "csrf_token": _token(client.get("/login").get_data(as_text=True)),
        },
    )
    cookie = page.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Secure" not in cookie
    assert client.get("/salir").status_code == 405


def test_carga_actualiza_sin_duplicar_y_un_error_no_escribe(client, app):
    panel = _login(client)
    assert "A quién ver primero" in panel.get_data(as_text=True)
    assert _count(app) == 0

    bad = _upload(client, workbook_bytes([valid_row(), valid_row(nombre="")]))
    assert "No se importó nada" in bad.get_data(as_text=True)
    assert _count(app) == 0

    ok = _upload(client, workbook_bytes([valid_row(nombre="Ana & Nia")]))
    body = ok.get_data(as_text=True)
    assert "Ana &amp; Nia" in body
    assert _count(app) == 1

    again = _upload(client, workbook_bytes([valid_row(nombre="Ana & Nia", promedio=1.2, semestre=1, materias_perdidas=4, inasistencias=8, evaluaciones_no_presentadas=3)]))
    assert "0 estudiantes nuevos y 1 actualizados" in again.get_data(as_text=True)
    assert _count(app) == 1
    with app.app_context():
        student = db.session.scalar(select(Student))
        assert student.risk_level == "Crítico"

    untouched = _upload(client, workbook_bytes([valid_row(promedio="alto")]))
    assert "No se importó nada" in untouched.get_data(as_text=True)
    with app.app_context():
        student = db.session.scalar(select(Student))
        assert float(student.promedio) == 1.2


def test_pdf_y_rechazo_de_extension(client):
    _login(client)
    _upload(
        client,
        workbook_bytes(
            [
                valid_row(
                    promedio=1.2,
                    semestre=1,
                    materias_perdidas=4,
                    inasistencias=8,
                    evaluaciones_no_presentadas=3,
                ),
                valid_row(documento="10001999", nombre="Luis Bajo", promedio=4.5),
            ]
        ),
    )
    rejected = _upload(client, b"no", name="notas.xlsm")
    assert "Solo se acepta" in rejected.get_data(as_text=True)

    report = client.get("/reporte.pdf")
    assert report.status_code == 200
    assert report.mimetype == "application/pdf"
    assert report.data.startswith(b"%PDF")
    assert b"10001001" in report.data
    assert b"10001999" not in report.data


def test_limite_de_intentos(client):
    for _ in range(5):
        page = client.get("/login")
        response = client.post(
            "/login",
            data={"email": "permanencia@uniminuto.local", "password": "clave-incorrecta", "csrf_token": _token(page.get_data(as_text=True))},
        )
        assert "incorrectos" in response.get_data(as_text=True)
    locked = client.post(
        "/login",
        data={
            "email": "permanencia@uniminuto.local",
            "password": "clave-de-prueba-123",
            "csrf_token": _token(client.get("/login").get_data(as_text=True)),
        },
    )
    assert locked.status_code == 429
    assert "15 minutos" in locked.get_data(as_text=True)


def test_parse_no_deja_filas_si_hay_errores():
    rows, errors = parse_xlsx(workbook_bytes([valid_row(promedio="")]))
    assert rows == []
    assert errors
