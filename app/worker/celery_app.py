from celery import Celery

from app.core.config import get_settings


settings = get_settings()
celery_app = Celery(
    "yt_rising",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.timezone = "UTC"
celery_app.autodiscover_tasks(["app.tasks"])
celery_app.conf.beat_schedule = {
    "collect-hourly": {
        "task": "app.tasks.tasks.collect_task",
        "schedule": 60 * 60,
    },
    "poll-15-min": {
        "task": "app.tasks.tasks.poll_task",
        "schedule": 15 * 60,
    },
    "notify-daily": {
        "task": "app.tasks.tasks.notify_task",
        "schedule": 24 * 60 * 60,
    },
}
