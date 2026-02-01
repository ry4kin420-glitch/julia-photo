from sqlalchemy import Boolean, Column, Integer, String

from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    query = Column(String, nullable=False)
    region_code = Column(String, nullable=True)
    relevance_language = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
