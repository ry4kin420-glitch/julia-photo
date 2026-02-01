from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import HealthResponse, RisingVideo, SourceCreate, SourceRead
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.source import Source
from app.services.collector import build_metrics, collect_candidates, update_metrics
from app.services.scoring import score_videos

router = APIRouter()


def get_session():
    with SessionLocal() as session:
        yield session


def get_settings_dep():
    return get_settings()


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))


@router.get("/sources", response_model=list[SourceRead])
def list_sources(session: Session = Depends(get_session)):
    sources = session.execute(select(Source)).scalars().all()
    return sources


@router.post("/sources", response_model=SourceRead)
def create_source(payload: SourceCreate, session: Session = Depends(get_session)):
    exists = session.execute(select(Source).where(Source.name == payload.name)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Source name already exists")
    source = Source(
        name=payload.name,
        query=payload.query,
        region_code=payload.region_code,
        relevance_language=payload.relevance_language,
        is_active=payload.is_active,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.get("/rising", response_model=list[RisingVideo])
def rising(
    niche: str | None = None,
    window: str = "6h",
    limit: int = 20,
    session: Session = Depends(get_session),
):
    if not window.endswith("h"):
        raise HTTPException(status_code=400, detail="window should be like '6h'")
    hours = int(window[:-1])
    metrics = build_metrics(session, window_hours=hours, niche=niche)
    scored = score_videos(metrics)[:limit]
    return [
        RisingVideo(
            video_id=item.video_id,
            title=item.title,
            url=item.url,
            channel_id=item.channel_id,
            score=item.score,
            age_hours=item.age_hours,
            views_velocity=item.views_velocity,
            engagement_rate=item.engagement_rate,
            views_per_sub=item.views_per_sub,
        )
        for item in scored
    ]


@router.post("/run/collect")
def run_collect(niche: str | None = None, settings=Depends(get_settings_dep), session: Session = Depends(get_session)):
    added = collect_candidates(session, settings, niche)
    return {"added": added}


@router.post("/run/poll")
def run_poll(settings=Depends(get_settings_dep), session: Session = Depends(get_session)):
    snapshots = update_metrics(session, settings)
    return {"snapshots": snapshots}
