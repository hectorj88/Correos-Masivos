"""
Copia este archivo junto a tu script de envío masivo.
Variables de entorno necesarias (las mismas del servidor):
  FERNET_KEY, ADMIN_API_KEY, TRACKING_BASE_URL (ej: https://track.hi-tech-solutions.com.co)
Requiere: pip install cryptography requests
"""
import json
import os

import requests
from cryptography.fernet import Fernet

_fernet = Fernet(os.environ["FERNET_KEY"].encode())
BASE_URL = os.environ["TRACKING_BASE_URL"].rstrip("/")
ADMIN_API_KEY = os.environ["ADMIN_API_KEY"]


def build_pixel_url(campaign_id: str, email: str) -> str:
    payload = json.dumps(
        {"c": campaign_id, "e": email.strip().lower()}, separators=(",", ":")
    ).encode()
    return f"{BASE_URL}/t/{_fernet.encrypt(payload).decode()}.gif"


def register_campaign(campaign_id: str, name: str, total_sent: int) -> dict:
    """Llamar al terminar el envío con el total de correos enviados correctamente."""
    r = requests.post(
        f"{BASE_URL}/admin/campaigns",
        json={"id": campaign_id, "name": name, "total_sent": total_sent},
        headers={"X-API-Key": ADMIN_API_KEY},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()
