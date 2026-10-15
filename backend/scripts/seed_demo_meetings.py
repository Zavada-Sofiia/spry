"""Explicit script to seed demo meetings for report generation and testing."""
from datetime import datetime, timedelta
import os
import sys

# Ensure /app or backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, SessionLocal, engine
from app.models import Meeting
from app.reports.weekly import TZ, week_bounds


def seed_demo_meetings(week: str = "2026-W41"):
    Base.metadata.create_all(bind=engine)
    week_start, _ = week_bounds(week)
    prev_week_start = week_start - timedelta(days=7)

    with SessionLocal() as session:
        if session.query(Meeting).count() > 0:
            print(f"Meetings table already contains {session.query(Meeting).count()} rows. Skipping seed.")
            return

        sample_meetings = [
            Meeting(
                title="Sprint Planning",
                starts_at=prev_week_start + timedelta(days=1, hours=10),
                ends_at=prev_week_start + timedelta(days=1, hours=12),
                attendee_count=8,
            ),
            Meeting(
                title="Design Review",
                starts_at=prev_week_start + timedelta(days=3, hours=14),
                ends_at=prev_week_start + timedelta(days=3, hours=15, minutes=30),
                attendee_count=4,
            ),
            Meeting(
                title="Weekly Sync",
                starts_at=week_start + timedelta(days=0, hours=10),
                ends_at=week_start + timedelta(days=0, hours=11),
                attendee_count=12,
            ),
            Meeting(
                title="Architecture Workshop",
                starts_at=week_start + timedelta(days=2, hours=13),
                ends_at=week_start + timedelta(days=2, hours=16),
                attendee_count=6,
            ),
            Meeting(
                title="Team Retrospective",
                starts_at=week_start + timedelta(days=4, hours=16),
                ends_at=week_start + timedelta(days=4, hours=17),
                attendee_count=10,
            ),
        ]
        session.add_all(sample_meetings)
        session.commit()
        print(f"Successfully seeded {len(sample_meetings)} demo meetings into the database.")


if __name__ == "__main__":
    week_arg = sys.argv[1] if len(sys.argv) > 1 else "2026-W41"
    seed_demo_meetings(week_arg)
