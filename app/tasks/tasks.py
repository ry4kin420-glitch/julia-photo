from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.alert_sent import AlertSent
from app.models.source import Source
from app.services.collector import build_metrics, collect_candidates, update_metrics
from app.services.scoring import score_videos
from app.services.telegram import format_message, send_message


@shared_task
def collect_task(niche: str | None = None) -> int:
    settings = get_settings()
    with SessionLocal() as session:
        return collect_candidates(session, settings, niche)


@shared_task
def poll_task() -> int:
    settings = get_settings()
    with SessionLocal() as session:
        return update_metrics(session, settings)


@shared_task
def notify_task(niche: str | None = None) -> int:
    settings = get_settings()
    if not settings.tg_bot_token or not settings.tg_chat_id:
        return 0
    with SessionLocal() as session:
        if niche is None:
            source = session.execute(select(Source).where(Source.is_active.is_(True))).scalars().first()
            niche = source.name if source else "default"
        metrics = build_metrics(session, window_hours=6, niche=niche)
        scored = score_videos(metrics)[:10]
        payload = [
            {
                "title": item.title,
                "score": item.score,
                "views_velocity": item.views_velocity,
                "age_hours": item.age_hours,
                "engagement_rate": item.engagement_rate,
                "url": item.url,
            }
            for item in scored
        ]
        message = format_message(niche, payload, datetime.now(timezone.utc))

        exists = session.execute(
            select(AlertSent).where(AlertSent.payload_hash == message.payload_hash)
        ).scalar_one_or_none()
        if exists:
            return 0

        send_message(settings.tg_bot_token, settings.tg_chat_id, message.text)
        session.add(
            AlertSent(
                sent_at=datetime.now(timezone.utc),
                chat_id=settings.tg_chat_id,
                payload_hash=message.payload_hash,
            )
        )
        session.commit()
        return len(scored)
