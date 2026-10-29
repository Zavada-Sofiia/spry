from sqlalchemy.orm import Session
from app import models, schemas


def get_meetings(db: Session):
    return db.query(models.Meeting).order_by(models.Meeting.starts_at.asc()).all()


def create_meeting(db: Session, meeting: schemas.MeetingCreate):
    db_meeting = models.Meeting(
        title=meeting.title,
        starts_at=meeting.starts_at,
        ends_at=meeting.ends_at,
        attendee_count=meeting.attendee_count,
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


def get_agendas(db: Session, meeting_id: int | None = None):
    query = db.query(models.Agenda)
    if meeting_id is not None:
        query = query.filter(models.Agenda.meeting_id == meeting_id)
    return query.order_by(models.Agenda.id.desc()).all()


def get_agenda(db: Session, agenda_id: int):
    return db.query(models.Agenda).filter(models.Agenda.id == agenda_id).first()


def create_agenda(db: Session, agenda: schemas.AgendaCreate):
    items_data = [item.model_dump() for item in agenda.items]
    action_items_data = [item.model_dump(mode="json") for item in agenda.action_items]

    ai_sugg = agenda.ai_suggestion
    if hasattr(ai_sugg, "model_dump"):
        ai_sugg = ai_sugg.model_dump(mode="json")

    db_agenda = models.Agenda(
        meeting_id=agenda.meeting_id,
        title=agenda.title,
        starts_at=agenda.starts_at,
        duration_minutes=agenda.duration_minutes,
        items=items_data,
        action_items=action_items_data,
        language=agenda.language,
        ai_suggestion=ai_sugg,
        model=agenda.model,
        prompt_version=agenda.prompt_version,
    )
    db.add(db_agenda)
    db.commit()
    db.refresh(db_agenda)
    return db_agenda
