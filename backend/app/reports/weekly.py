import csv
from datetime import date, datetime, timedelta
import io
import os
import re
from typing import Optional
import urllib.parse
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Meeting

TZ = ZoneInfo("Europe/Kyiv")
ISO_WEEK_REGEX = re.compile(r"^\d{4}-W(0[1-9]|[1-4]\d|5[0-3])$")

_report_engine = None


def get_report_engine():
    global _report_engine
    if _report_engine is not None:
        return _report_engine

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        from app.database import engine

        return engine

    parsed = urllib.parse.urlparse(db_url)
    hostname = parsed.hostname or ""

    # If targeting RDS Aurora without password in URL, use dynamic IAM DB authentication
    if "rds.amazonaws.com" in hostname and not parsed.password:
        import boto3
        from sqlalchemy import event

        region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "eu-north-1"))
        user = parsed.username or "postgres"
        port = parsed.port or 5432
        dbname = parsed.path.lstrip("/") or "postgres"

        connect_url = f"postgresql+psycopg2://{user}@{hostname}:{port}/{dbname}?sslmode=require"
        engine = create_engine(connect_url, pool_pre_ping=True)

        rds_client = boto3.client("rds", region_name=region)

        @event.listens_for(engine, "do_connect")
        def provide_token(dialect, conn_rec, cargs, cparams):
            cparams["password"] = rds_client.generate_db_auth_token(
                DBHostname=hostname,
                Port=port,
                DBUsername=user,
                Region=region,
            )

        _report_engine = engine
        return _report_engine

    _report_engine = create_engine(db_url)
    return _report_engine


def get_report_session() -> Session:
    eng = get_report_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)()


def validate_week(week: str) -> None:
    """Validate that the week matches the ISO-8601 week pattern (e.g. 2026-W40)."""
    if not isinstance(week, str) or not ISO_WEEK_REGEX.match(week):
        raise ValueError(
            f"Invalid ISO week format '{week}'. Expected format 'YYYY-Www' (e.g. '2026-W40')."
        )


def week_bounds(week: str) -> tuple[datetime, datetime]:
    """'2026-W40' -> (Monday 00:00, next Monday 00:00) in Europe/Kyiv."""
    validate_week(week)
    monday = datetime.strptime(f"{week}-1", "%G-W%V-%u").replace(tzinfo=TZ)
    return monday, monday + timedelta(days=7)


def iso_week_of(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def previous_iso_week(today: Optional[date] = None) -> str:
    today = today or datetime.now(TZ).date()
    return iso_week_of(today - timedelta(days=7))


def report_key(week: str) -> str:
    validate_week(week)
    return f"reports/{week}.csv"


def _format_change_pct(current: float, previous: float) -> str:
    if previous == 0:
        return "N/A"
    pct = ((current - previous) / previous) * 100.0
    return f"{pct:+.1f}%"


def _duration_hours(m: Meeting) -> float:
    seconds = (m.ends_at - m.starts_at).total_seconds()
    return max(0.0, seconds / 3600.0)


def _generate_report_csv(
    week: str,
    prev_week: str,
    current_meetings: list[Meeting],
    prev_meetings: list[Meeting],
) -> bytes:
    curr_count = len(current_meetings)
    curr_hours = round(sum(_duration_hours(m) for m in current_meetings), 2)

    prev_count = len(prev_meetings)
    prev_hours = round(sum(_duration_hours(m) for m in prev_meetings), 2)

    count_change = curr_count - prev_count
    hours_change = round(curr_hours - prev_hours, 2)
    count_pct = _format_change_pct(curr_count, prev_count)
    hours_pct = _format_change_pct(curr_hours, prev_hours)

    # Sort meetings: longest duration descending, deterministic tie-break on id ascending
    sorted_meetings = sorted(
        current_meetings,
        key=lambda m: (-_duration_hours(m), m.id if m.id is not None else 0),
    )
    top_meetings = sorted_meetings[:5]

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    # Section 1: Summary metrics
    writer.writerow(["section", "metric", "value"])
    writer.writerow(["summary", "week", week])
    writer.writerow(["summary", "meetings", curr_count])
    writer.writerow(["summary", "total_hours", f"{curr_hours:.2f}"])

    writer.writerow(["previous_week", "week", prev_week])
    writer.writerow(["previous_week", "meetings", prev_count])
    writer.writerow(["previous_week", "total_hours", f"{prev_hours:.2f}"])

    writer.writerow(["change", "meetings", f"{count_change:+d}"])
    writer.writerow(["change", "meetings_pct", count_pct])
    writer.writerow(["change", "total_hours", f"{hours_change:+.2f}"])
    writer.writerow(["change", "total_hours_pct", hours_pct])

    # Blank separator line
    writer.writerow([])

    # Section 2: Top longest meetings
    writer.writerow(["top_meetings", "title", "start", "duration_hours", "participants"])
    for m in top_meetings:
        dur = _duration_hours(m)
        start_str = m.starts_at.isoformat() if hasattr(m.starts_at, "isoformat") else str(m.starts_at)
        writer.writerow([
            "top_meeting",
            m.title,
            start_str,
            f"{dur:.2f}",
            m.attendee_count,
        ])

    return output.getvalue().encode("utf-8")


def build_weekly_report(week: str, db: Optional[Session] = None) -> bytes:
    """Query the meetings of one ISO week (e.g. '2026-W40') and return the CSV."""
    validate_week(week)
    week_start, week_end = week_bounds(week)
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = week_start
    prev_week_str = iso_week_of(prev_week_start.date())

    def _execute(session: Session) -> bytes:
        current_meetings = (
            session.query(Meeting)
            .filter(Meeting.starts_at >= week_start, Meeting.starts_at < week_end)
            .all()
        )
        prev_meetings = (
            session.query(Meeting)
            .filter(Meeting.starts_at >= prev_week_start, Meeting.starts_at < prev_week_end)
            .all()
        )
        return _generate_report_csv(week, prev_week_str, current_meetings, prev_meetings)

    if db is not None:
        return _execute(db)

    with get_report_session() as session:
        return _execute(session)
