"""Small client for local Metabase, with private credentials."""
from getpass import getpass
import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

class MetabaseClient:
    def __init__(self):
        load_dotenv(ROOT / ".env")
        self.url = os.environ.get("METABASE_URL", "http://localhost:8000").rstrip("/")
        self.session = requests.Session()
        credentials_file = ROOT / ".secrets" / "metabase.json"
        local = json.loads(credentials_file.read_text()) if credentials_file.exists() else {}
        email = os.environ.get("METABASE_EMAIL") or local.get("email") or input("Metabase login email: ").strip()
        password = os.environ.get("METABASE_PASSWORD") or local.get("password") or getpass("Metabase password (hidden): ")
        result = self.request("POST", "/api/session", {"username": email, "password": password})
        self.session.headers["X-Metabase-Session"] = result["id"]

    def request(self, method, path, data=None):
        response = self.session.request(method, self.url + path, json=data, timeout=120)
        response.raise_for_status()
        return response.json() if response.content else None
