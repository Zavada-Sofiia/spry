from sqlalchemy.orm import Session
from app import models, schemas

def get_meetings(db: Session):
    return db.query(models.Meeting).order_by(models.Meeting.starts_at.asc()).all()

def create_meeting(db: Session, meeting: schemas.MeetingCreate):
    db_meeting = models.Meeting(
        title=meeting.title,
        starts_at=meeting.starts_at,
        ends_at=meeting.ends_at,
        attendee_count=meeting.attendee_count
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting
