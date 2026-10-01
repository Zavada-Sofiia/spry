from datetime import datetime
from pydantic import BaseModel, Field

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
