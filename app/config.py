import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

ROOT = Path(__file__).resolve().parent.parent


def load_local_env() -> None:
    """Load a local .env without overriding variables already set in the shell."""
    path = ROOT / ".env"
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta la variable de entorno {name}.")
    return value


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    scheme, sep, rest = url.partition("://")
    if sep and scheme == "postgresql":
        url = "postgresql+psycopg://" + rest

    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host.endswith("render.com") and "sslmode=" not in parsed.query:
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["sslmode"] = "require"
        parsed = parsed._replace(query=urlencode(query))
        url = urlunparse(parsed)
    return url


def build_config() -> dict:
    on_render = os.environ.get("RENDER") == "true"
    return {
        "SECRET_KEY": require_env("SECRET_KEY"),
        "SQLALCHEMY_DATABASE_URI": normalize_database_url(require_env("DATABASE_URL")),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": 5},
        },
        "MAX_CONTENT_LENGTH": 2 * 1024 * 1024,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": on_render,
        "WTF_CSRF_SSL_STRICT": on_render,
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=8),
        "PREFERRED_URL_SCHEME": "https" if on_render else "http",
    }
