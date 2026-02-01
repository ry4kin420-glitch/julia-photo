from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class Channel(Base):
    __tablename__ = "channels"

    channel_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    subscriber_count = Column(Integer, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
