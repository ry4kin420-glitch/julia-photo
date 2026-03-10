from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class AlertSent(Base):
    __tablename__ = "alerts_sent"

    id = Column(Integer, primary_key=True)
    sent_at = Column(DateTime, nullable=False)
    chat_id = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False, unique=True)
