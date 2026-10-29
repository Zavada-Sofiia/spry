from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app import crud, schemas, models

# Ensure tables exist
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: could not create tables on startup: {e}")

app = FastAPI(title="Spry API")

origins = [
    "https://d1pk13cbcfrq49.cloudfront.net/",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/meetings", response_model=List[schemas.MeetingResponse])
def read_meetings(db: Session = Depends(get_db)):
    return crud.get_meetings(db)

@app.post("/api/meetings", response_model=schemas.MeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting(meeting: schemas.MeetingCreate, db: Session = Depends(get_db)):
    return crud.create_meeting(db=db, meeting=meeting)

@app.get("/api/agendas", response_model=List[schemas.AgendaResponse])
def read_agendas(meeting_id: Optional[int] = None, db: Session = Depends(get_db)):
    return crud.get_agendas(db=db, meeting_id=meeting_id)

@app.get("/api/agendas/{agenda_id}", response_model=schemas.AgendaResponse)
def read_agenda(agenda_id: int, db: Session = Depends(get_db)):
    agenda = crud.get_agenda(db=db, agenda_id=agenda_id)
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda not found")
    return agenda

@app.post("/api/agendas", response_model=schemas.AgendaResponse, status_code=status.HTTP_201_CREATED)
def create_agenda(agenda: schemas.AgendaCreate, db: Session = Depends(get_db)):
    return crud.create_agenda(db=db, agenda=agenda)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
