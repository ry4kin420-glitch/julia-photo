from datetime import datetime, timezone

from app.services.telegram import format_message


def test_format_message_contains_items():
    payload = [
        {
            "title": "Test video",
            "score": 5.5,
            "views_velocity": 120.0,
            "age_hours": 3.2,
            "engagement_rate": 0.04,
            "url": "https://youtube.com/watch?v=123",
        }
    ]

    message = format_message("ai", payload, datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc))

    assert "Rising videos" in message.text
    assert "Test video" in message.text
    assert "https://youtube.com/watch?v=123" in message.text
    assert message.payload_hash
