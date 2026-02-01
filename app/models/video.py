from sqlalchemy import Column, DateTime, String

from app.db.base import Base


class Video(Base):
    __tablename__ = "videos"

    video_id = Column(String, primary_key=True)
    channel_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    category_id = Column(String, nullable=True)
    first_seen_at = Column(DateTime, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)
    source_name = Column(String, nullable=True)
