from datetime import datetime

from pydantic import BaseModel


class SourceCreate(BaseModel):
    name: str
    query: str
    region_code: str | None = None
    relevance_language: str | None = None
    is_active: bool = True


class SourceRead(BaseModel):
    id: int
    name: str
    query: str
    region_code: str | None = None
    relevance_language: str | None = None
    is_active: bool

    class Config:
        from_attributes = True


class RisingVideo(BaseModel):
    video_id: str
    title: str
    url: str
    channel_id: str
    score: float
    age_hours: float
    views_velocity: float
    engagement_rate: float
    views_per_sub: float


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
