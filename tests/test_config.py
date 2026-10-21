from app.config import normalize_database_url


def test_convierte_la_url_interna_de_render_a_psycopg_con_tls():
    url = normalize_database_url("postgres://antes:secreto@dpg-abc-a.oregon-postgres.render.com/antes")
    assert url.startswith("postgresql+psycopg://")
    assert "sslmode=require" in url


def test_la_url_local_no_exige_ssl():
    url = normalize_database_url("postgresql://antes:antes@localhost:5432/antes")
    assert url == "postgresql+psycopg://antes:antes@localhost:5432/antes"
    assert "sslmode" not in url
