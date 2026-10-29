from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    attendee_count = Column(Integer, nullable=False)

    agendas = relationship("Agenda", back_populates="meeting", cascade="all, delete-orphan")


class Agenda(Base):
    __tablename__ = "agendas"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    items = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=list)
    action_items = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=list)
    language = Column(String, nullable=False, default="en")
    ai_suggestion = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    model = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)

    meeting = relationship("Meeting", back_populates="agendas")
