from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.db.base import Base


class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"

    id = Column(Integer, primary_key=True)
    video_id = Column(String, ForeignKey("videos.video_id"), nullable=False)
    taken_at = Column(DateTime, nullable=False)
    views = Column(Integer, nullable=False)
    likes = Column(Integer, nullable=False)
    comments = Column(Integer, nullable=False)
    subscriber_count_at_time = Column(Integer, nullable=False)
    raw_json_s3_key = Column(String, nullable=True)
