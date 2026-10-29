from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, Field


class AgendaItemSchema(BaseModel):
    topic: str = Field(min_length=1)
    owner: str | None = None
    minutes: int | None = Field(default=None, ge=1, le=480)


class ActionItemSchema(BaseModel):
    task: str = Field(min_length=1)
    owner: str | None = None
    due: str | None = None


class AgendaBase(BaseModel):
    meeting_id: int | None = None
    title: str | None = None
    starts_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=600)
    items: list[AgendaItemSchema] = []
    action_items: list[ActionItemSchema] = []
    language: str = "en"


class AgendaCreate(AgendaBase):
    ai_suggestion: Any | None = None
    model: str | None = None
    prompt_version: str | None = None


class AgendaResponse(AgendaBase):
    id: int
    ai_suggestion: Any | None = None
    model: str | None = None
    prompt_version: str | None = None

    class Config:
        from_attributes = True


class MeetingBase(BaseModel):
    title: str = Field(..., example="Sprint Planning")
    starts_at: datetime = Field(..., example="2026-10-15T09:00:00Z")
    ends_at: datetime = Field(..., example="2026-10-15T10:00:00Z")
    attendee_count: int = Field(..., ge=1, example=5)


class MeetingCreate(MeetingBase):
    pass


class MeetingResponse(MeetingBase):
    id: int

    class Config:
        from_attributes = True
