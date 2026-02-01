from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.channel import Channel
from app.models.source import Source
from app.models.video import Video
from app.models.video_snapshot import VideoSnapshot
from app.services.storage import S3Config, build_s3_client, store_json
from app.services.youtube_client import channels_list, search_list, videos_list


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _parse_datetime(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _get_s3(settings: Settings):
    if not (settings.s3_endpoint and settings.s3_key and settings.s3_secret and settings.s3_bucket):
        return None
    config = S3Config(
        endpoint=settings.s3_endpoint,
        key=settings.s3_key,
        secret=settings.s3_secret,
        bucket=settings.s3_bucket,
    )
    return build_s3_client(config), config.bucket


def collect_candidates(session: Session, settings: Settings, niche: str | None = None) -> int:
    query = select(Source).where(Source.is_active.is_(True))
    if niche:
        query = query.where(Source.name == niche)
    sources = session.execute(query).scalars().all()
    if not sources:
        return 0

    now = _utc_now()
    published_after = (now - dt.timedelta(hours=48)).isoformat().replace("+00:00", "Z")
    added = 0

    for source in sources:
        payload = search_list(
            api_key=settings.yt_api_key,
            query=source.query,
            published_after=published_after,
            region_code=source.region_code,
            relevance_language=source.relevance_language,
        )
        for item in payload.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            exists = session.get(Video, video_id)
            if exists:
                continue
            snippet = item.get("snippet", {})
            published_at = _parse_datetime(snippet.get("publishedAt"))
            video = Video(
                video_id=video_id,
                channel_id=snippet.get("channelId"),
                title=snippet.get("title", ""),
                published_at=published_at,
                url=f"https://www.youtube.com/watch?v={video_id}",
                thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
                category_id=None,
                first_seen_at=now,
                last_checked_at=None,
                source_name=source.name,
            )
            session.add(video)
            added += 1
    session.commit()
    return added


def update_metrics(session: Session, settings: Settings, max_age_hours: int = 72) -> int:
    now = _utc_now()
    cutoff = now - dt.timedelta(hours=max_age_hours)

    videos = session.execute(
        select(Video).where(Video.published_at >= cutoff)
    ).scalars().all()
    if not videos:
        return 0

    s3 = _get_s3(settings)
    total_snapshots = 0

    for batch_start in range(0, len(videos), 50):
        batch = videos[batch_start : batch_start + 50]
        video_ids = [video.video_id for video in batch]
        payload = videos_list(settings.yt_api_key, video_ids)
        items = payload.get("items", [])

        channel_ids = {item.get("snippet", {}).get("channelId") for item in items}
        channel_ids.discard(None)

        channel_payload = {}
        if channel_ids:
            channel_payload = channels_list(settings.yt_api_key, list(channel_ids))
        channel_stats = {
            item.get("id"): item
            for item in channel_payload.get("items", [])
        }

        for item in items:
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})
            video_id = item.get("id")
            if not video_id:
                continue

            channel_id = snippet.get("channelId")
            channel_item = channel_stats.get(channel_id, {})
            channel_title = channel_item.get("snippet", {}).get("title", "")
            subscriber_count = int(channel_item.get("statistics", {}).get("subscriberCount", 0))

            channel = session.get(Channel, channel_id)
            if channel:
                channel.subscriber_count = subscriber_count
                channel.last_checked_at = now
            else:
                session.add(
                    Channel(
                        channel_id=channel_id,
                        title=channel_title,
                        subscriber_count=subscriber_count,
                        last_checked_at=now,
                    )
                )

            raw_key = None
            if s3:
                client, bucket = s3
                raw_key = (
                    f"raw/youtube/videos/{video_id}/{now.date().isoformat()}/{now.strftime('%H%M')}.json"
                )
                store_json(client, bucket, raw_key, item)

            snapshot = VideoSnapshot(
                video_id=video_id,
                taken_at=now,
                views=int(stats.get("viewCount", 0)),
                likes=int(stats.get("likeCount", 0)),
                comments=int(stats.get("commentCount", 0)),
                subscriber_count_at_time=subscriber_count,
                raw_json_s3_key=raw_key,
            )
            session.add(snapshot)
            total_snapshots += 1

            video = session.get(Video, video_id)
            if video:
                video.last_checked_at = now
                video.title = snippet.get("title", video.title)
                video.channel_id = channel_id or video.channel_id
                video.thumbnail_url = snippet.get("thumbnails", {}).get("high", {}).get("url")
                video.category_id = snippet.get("categoryId", video.category_id)

        session.commit()
    return total_snapshots


def load_snapshots(session: Session, video_id: str, window_hours: int) -> list[VideoSnapshot]:
    now = _utc_now()
    cutoff = now - dt.timedelta(hours=window_hours)
    snapshots = session.execute(
        select(VideoSnapshot)
        .where(VideoSnapshot.video_id == video_id)
        .where(VideoSnapshot.taken_at >= cutoff)
        .order_by(VideoSnapshot.taken_at.asc())
    ).scalars().all()
    return snapshots


def build_metrics(session: Session, window_hours: int, niche: str | None = None):
    from app.services.scoring import VideoMetrics, compute_velocity

    now = _utc_now()
    query = select(Video)
    if niche:
        query = query.where(Video.source_name == niche)
    videos = session.execute(query).scalars().all()

    metrics: list[VideoMetrics] = []
    for video in videos:
        snapshots = load_snapshots(session, video.video_id, window_hours)
        if len(snapshots) < 2:
            continue
        oldest = snapshots[0]
        latest = snapshots[-1]
        views_vel, likes_vel, comments_vel = compute_velocity(latest, oldest)
        engagement = 0.0
        if latest.views > 0:
            engagement = (latest.likes + latest.comments) / latest.views
        views_per_sub = latest.views / max(latest.subscriber_count_at_time, 1)
        age_hours = (now - video.published_at).total_seconds() / 3600
        metrics.append(
            VideoMetrics(
                video_id=video.video_id,
                channel_id=video.channel_id,
                title=video.title,
                url=video.url,
                published_at=video.published_at,
                views_velocity=views_vel,
                likes_velocity=likes_vel,
                comments_velocity=comments_vel,
                engagement_rate=engagement,
                views_per_sub=views_per_sub,
                age_hours=age_hours,
            )
        )
    return metrics
