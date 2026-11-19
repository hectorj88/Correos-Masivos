import base64
import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from core.security import decode_token
from services import tracking_service

logger = logging.getLogger("tracking")
router = APIRouter()

# GIF transparente de 1x1 px
PIXEL_GIF = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "X-Content-Type-Options": "nosniff",
}


@router.get("/t/{token}.gif", include_in_schema=False)
@limiter.limit("300/minute")  # holgado: Gmail/Apple agrupan muchas aperturas bajo pocas IPs
async def track_open(request: Request, token: str, db: AsyncSession = Depends(get_db)):
    decoded = decode_token(token)
    if decoded:
        campaign_id, email = decoded
        try:
            await tracking_service.register_open(
                db,
                campaign_id=campaign_id,
                email=email,
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception:  # nunca romper la imagen por un fallo de BD
            logger.exception("No se pudo registrar la apertura")
    # Siempre la misma respuesta (token válido o no): no se filtra información a terceros.
    return Response(content=PIXEL_GIF, media_type="image/gif", headers=NO_CACHE_HEADERS)
