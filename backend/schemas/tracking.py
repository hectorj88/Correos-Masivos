from datetime import datetime

from pydantic import BaseModel, Field

CAMPAIGN_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"


class CampaignCreate(BaseModel):
    id: str = Field(pattern=CAMPAIGN_ID_PATTERN)
    name: str = Field(min_length=1, max_length=200)
    total_sent: int = Field(ge=0)


class CampaignStats(BaseModel):
    campaign_id: str
    name: str
    total_sent: int
    total_opens: int
    unique_opens: int
    open_rate_percent: float


class OpenerOut(BaseModel):
    email: str
    opens: int
    first_opened_at: datetime
