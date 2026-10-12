"""Read a private PostgreSQL connection for both dlt and dbt."""
import os
from getpass import getpass
from pathlib import Path
from urllib.parse import quote, urlparse, unquote, parse_qs
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

def configure_connection():
    load_dotenv(ROOT / ".env")
    url = os.environ.get("DATABASE_URL")
    if not url:
        password = os.environ.get("DATABASE_PASSWORD") or getpass("Supabase database password (hidden): ")
        host = os.environ.get("SUPABASE_HOST") or input("Supabase session pooler host: ").strip()
        user = os.environ.get("SUPABASE_USER") or input("Supabase database user: ").strip()
        port = os.environ.get("SUPABASE_PORT", "5432")
        database = os.environ.get("SUPABASE_DATABASE", "postgres")
        url = f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}@{host}:{port}/{database}?sslmode=require"
        os.environ["DATABASE_URL"] = url
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("A PostgreSQL connection URL is required.")
    os.environ.update({"PGHOST": parsed.hostname or "localhost", "PGPORT": str(parsed.port or 5432),
        "PGUSER": unquote(parsed.username or ""), "PGPASSWORD": unquote(parsed.password or ""),
        "PGDATABASE": unquote(parsed.path.lstrip("/")),
        "PGSSLMODE": parse_qs(parsed.query).get("sslmode", ["require"])[0]})
    return url
