from datetime import datetime, timedelta, timezone

from app.services.scoring import VideoMetrics, score_videos


def test_score_videos_orders_by_score():
    now = datetime.now(timezone.utc)
    metrics = [
        VideoMetrics(
            video_id="a",
            channel_id="c1",
            title="A",
            url="https://example.com/a",
            published_at=now,
            views_velocity=100,
            likes_velocity=10,
            comments_velocity=5,
            engagement_rate=0.05,
            views_per_sub=1.0,
            age_hours=5,
        ),
        VideoMetrics(
            video_id="b",
            channel_id="c2",
            title="B",
            url="https://example.com/b",
            published_at=now - timedelta(hours=10),
            views_velocity=10,
            likes_velocity=1,
            comments_velocity=0,
            engagement_rate=0.01,
            views_per_sub=0.1,
            age_hours=10,
        ),
    ]

    scored = score_videos(metrics)

    assert scored[0].video_id == "a"
    assert scored[0].score >= scored[1].score
