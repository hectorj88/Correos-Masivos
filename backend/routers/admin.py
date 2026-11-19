from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import require_api_key
from schemas.tracking import CAMPAIGN_ID_PATTERN, CampaignCreate, CampaignStats, OpenerOut
from services import tracking_service

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_api_key)]
)


@router.post("/campaigns", response_model=CampaignStats, status_code=201)
async def upsert_campaign(body: CampaignCreate, db: AsyncSession = Depends(get_db)):
    """Crea/actualiza la campaña con el total de correos enviados (base de la tasa de apertura)."""
    await tracking_service.upsert_campaign(db, body.id, body.name, body.total_sent)
    return await tracking_service.get_campaign_stats(db, body.id)


@router.get("/campaigns/{campaign_id}/stats", response_model=CampaignStats)
async def campaign_stats(
    campaign_id: str = Path(pattern=CAMPAIGN_ID_PATTERN),
    db: AsyncSession = Depends(get_db),
):
    stats = await tracking_service.get_campaign_stats(db, campaign_id)
    if not stats:
        raise HTTPException(404, "Campaña no encontrada")
    return stats


@router.get("/campaigns/{campaign_id}/openers", response_model=list[OpenerOut])
async def campaign_openers(
    campaign_id: str = Path(pattern=CAMPAIGN_ID_PATTERN),
    db: AsyncSession = Depends(get_db),
):
    """Quiénes abrieron el correo (útil para el seguimiento comercial)."""
    return await tracking_service.get_openers(db, campaign_id)
