from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.open_event import Campaign, EmailOpen


async def register_open(
    db: AsyncSession,
    campaign_id: str,
    email: str,
    ip: str | None,
    user_agent: str | None,
) -> bool:
    """Registra una apertura. Devuelve False si se ignoró por duplicada (ventana anti-spam)."""
    if settings.dedupe_seconds > 0:
        since = datetime.now(timezone.utc) - timedelta(seconds=settings.dedupe_seconds)
        recent = await db.scalar(
            select(EmailOpen.id)
            .where(
                EmailOpen.campaign_id == campaign_id,
                EmailOpen.email == email,
                EmailOpen.opened_at >= since,
            )
            .limit(1)
        )
        if recent:
            return False

    db.add(
        EmailOpen(
            campaign_id=campaign_id,
            email=email,
            ip_address=ip if settings.store_ip else None,
            user_agent=(user_agent or "")[:255] or None,
        )
    )
    await db.commit()
    return True


async def upsert_campaign(
    db: AsyncSession, campaign_id: str, name: str, total_sent: int
) -> None:
    campaign = await db.get(Campaign, campaign_id)
    if campaign:
        campaign.name = name
        campaign.total_sent = total_sent
    else:
        db.add(Campaign(id=campaign_id, name=name, total_sent=total_sent))
    await db.commit()


async def get_campaign_stats(db: AsyncSession, campaign_id: str) -> dict | None:
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        return None
    total_opens, unique_opens = (
        await db.execute(
            select(
                func.count(EmailOpen.id), func.count(func.distinct(EmailOpen.email))
            ).where(EmailOpen.campaign_id == campaign_id)
        )
    ).one()
    rate = (
        round(unique_opens / campaign.total_sent * 100, 2) if campaign.total_sent else 0.0
    )
    return {
        "campaign_id": campaign.id,
        "name": campaign.name,
        "total_sent": campaign.total_sent,
        "total_opens": total_opens,
        "unique_opens": unique_opens,
        "open_rate_percent": rate,
    }


async def get_openers(db: AsyncSession, campaign_id: str) -> list[dict]:
    rows = await db.execute(
        select(
            EmailOpen.email,
            func.count(EmailOpen.id).label("opens"),
            func.min(EmailOpen.opened_at).label("first_opened_at"),
        )
        .where(EmailOpen.campaign_id == campaign_id)
        .group_by(EmailOpen.email)
        .order_by(func.min(EmailOpen.opened_at))
    )
    return [
        {"email": r.email, "opens": r.opens, "first_opened_at": r.first_opened_at}
        for r in rows
    ]
