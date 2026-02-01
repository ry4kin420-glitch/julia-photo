from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from app.models.video_snapshot import VideoSnapshot


@dataclass
class VideoMetrics:
    video_id: str
    channel_id: str
    title: str
    url: str
    published_at: datetime
    views_velocity: float
    likes_velocity: float
    comments_velocity: float
    engagement_rate: float
    views_per_sub: float
    age_hours: float


@dataclass
class ScoredVideo:
    video_id: str
    title: str
    url: str
    channel_id: str
    score: float
    views_velocity: float
    engagement_rate: float
    views_per_sub: float
    age_hours: float


def compute_velocity(latest: VideoSnapshot, oldest: VideoSnapshot) -> tuple[float, float, float]:
    delta_views = latest.views - oldest.views
    delta_likes = latest.likes - oldest.likes
    delta_comments = latest.comments - oldest.comments
    delta_hours = max((latest.taken_at - oldest.taken_at).total_seconds() / 3600, 1e-6)
    return (
        delta_views / delta_hours,
        delta_likes / delta_hours,
        delta_comments / delta_hours,
    )


def age_boost(age_hours: float) -> float:
    if age_hours <= 48:
        return 1.0 + (48 - age_hours) / 96
    return 1.0


def z_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = math.sqrt(variance) or 1.0
    return [(value - mean) / std for value in values]


def score_videos(metrics: list[VideoMetrics]) -> list[ScoredVideo]:
    if not metrics:
        return []

    views_z = z_scores([m.views_velocity for m in metrics])
    likes_z = z_scores([m.likes_velocity for m in metrics])
    comments_z = z_scores([m.comments_velocity for m in metrics])
    views_per_sub_z = z_scores([m.views_per_sub for m in metrics])
    engagement_z = z_scores([m.engagement_rate for m in metrics])

    scored: list[ScoredVideo] = []
    for metric, vz, lz, cz, vpsz, ez in zip(
        metrics, views_z, likes_z, comments_z, views_per_sub_z, engagement_z
    ):
        score = (
            0.45 * vz
            + 0.20 * lz
            + 0.15 * cz
            + 0.10 * vpsz
            + 0.10 * ez
        ) * age_boost(metric.age_hours)
        scored.append(
            ScoredVideo(
                video_id=metric.video_id,
                title=metric.title,
                url=metric.url,
                channel_id=metric.channel_id,
                score=score,
                views_velocity=metric.views_velocity,
                engagement_rate=metric.engagement_rate,
                views_per_sub=metric.views_per_sub,
                age_hours=metric.age_hours,
            )
        )
    return sorted(scored, key=lambda item: item.score, reverse=True)
