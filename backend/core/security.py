import json
import secrets

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Header, HTTPException, status

from core.config import settings

# Fernet = cifrado autenticado: el token oculta el correo y no se puede falsificar ni modificar.
_fernet = Fernet(settings.fernet_key.encode())

MAX_TOKEN_LENGTH = 512


def create_token(campaign_id: str, email: str) -> str:
    payload = json.dumps(
        {"c": campaign_id, "e": email.strip().lower()}, separators=(",", ":")
    ).encode()
    return _fernet.encrypt(payload).decode()


def decode_token(token: str) -> tuple[str, str] | None:
    """Devuelve (campaign_id, email) o None si el token es inválido/manipulado."""
    if not token or len(token) > MAX_TOKEN_LENGTH:
        return None
    try:
        data = json.loads(_fernet.decrypt(token.encode()))
        return str(data["c"]), str(data["e"])
    except (InvalidToken, ValueError, KeyError, TypeError):
        return None


async def require_api_key(x_api_key: str = Header(default="")) -> None:
    """Protege los endpoints administrativos (comparación en tiempo constante)."""
    if not secrets.compare_digest(
        x_api_key.encode(), settings.admin_api_key.encode()
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autorizado")
