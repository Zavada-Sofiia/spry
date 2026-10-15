import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import unittest
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Meeting
from app.reports.weekly import (
    TZ,
    build_weekly_report,
    iso_week_of,
    previous_iso_week,
    report_key,
    validate_week,
    week_bounds,
)


class TestWeeklyReportUnit(unittest.TestCase):
    def test_week_bounds(self):
        start, end = week_bounds("2026-W40")
        self.assertEqual(start.tzinfo, TZ)
        self.assertEqual(end.tzinfo, TZ)
        # 2026-W40 Monday is 2026-09-28
        self.assertEqual(start.year, 2026)
        self.assertEqual(start.month, 9)
        self.assertEqual(start.day, 28)
        self.assertEqual(start.hour, 0)
        self.assertEqual(start.minute, 0)
        self.assertEqual(end - start, timedelta(days=7))

    def test_previous_iso_week_year_boundary(self):
        # 2027-01-04 is a Monday in week 2027-W01. Previous week should be 2026-W53.
        d = date(2027, 1, 4)
        prev = previous_iso_week(today=d)
        self.assertEqual(prev, "2026-W53")

    def test_iso_week_of(self):
        self.assertEqual(iso_week_of(date(2026, 10, 15)), "2026-W42")
        self.assertEqual(iso_week_of(date(2026, 1, 1)), "2026-W01")

    def test_report_key(self):
        self.assertEqual(report_key("2026-W40"), "reports/2026-W40.csv")

    def test_validate_week_bad_input(self):
        invalid_weeks = [
            "2026-40",
            "last_week",
            "2026-W00",
            "2026-W54",
            "26-W40",
            "",
            None,
            123,
        ]
        for val in invalid_weeks:
            with self.subTest(val=val):
                with self.assertRaises(ValueError):
                    validate_week(val)
                with self.assertRaises(ValueError):
                    report_key(val)
                with self.assertRaises(ValueError):
                    week_bounds(val)


class TestWeeklyReportGeneration(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_build_weekly_report_empty(self):
        csv_bytes = build_weekly_report("2026-W40", db=self.session)
        content = csv_bytes.decode("utf-8")
        self.assertIn("summary,week,2026-W40", content)
        self.assertIn("summary,meetings,0", content)
        self.assertIn("summary,total_hours,0.00", content)
        self.assertIn("previous_week,week,2026-W39", content)
        self.assertIn("change,meetings,+0", content)

    def test_build_weekly_report_with_data_and_idempotency(self):
        # 2026-W40: 2026-09-28 to 2026-10-05
        # 2026-W39: 2026-09-21 to 2026-09-28

        # Add meetings in previous week (W39)
        m_prev1 = Meeting(
            id=1,
            title="Prev Meeting 1",
            starts_at=datetime(2026, 9, 22, 10, 0, tzinfo=TZ),
            ends_at=datetime(2026, 9, 22, 11, 0, tzinfo=TZ),  # 1 hour
            attendee_count=3,
        )
        self.session.add(m_prev1)

        # Add meetings in target week (W40)
        m_curr1 = Meeting(
            id=2,
            title="Short Standup",
            starts_at=datetime(2026, 9, 29, 9, 0, tzinfo=TZ),
            ends_at=datetime(2026, 9, 29, 9, 30, tzinfo=TZ),  # 0.5 hour
            attendee_count=5,
        )
        m_curr2 = Meeting(
            id=3,
            title="Long Workshop",
            starts_at=datetime(2026, 9, 30, 14, 0, tzinfo=TZ),
            ends_at=datetime(2026, 9, 30, 17, 0, tzinfo=TZ),  # 3.0 hours
            attendee_count=8,
        )
        m_curr3 = Meeting(
            id=4,
            title="Sprint Planning",
            starts_at=datetime(2026, 10, 1, 10, 0, tzinfo=TZ),
            ends_at=datetime(2026, 10, 1, 12, 0, tzinfo=TZ),  # 2.0 hours
            attendee_count=10,
        )
        # Outside target week (W41)
        m_future = Meeting(
            id=5,
            title="Future Meeting",
            starts_at=datetime(2026, 10, 6, 10, 0, tzinfo=TZ),
            ends_at=datetime(2026, 10, 6, 11, 0, tzinfo=TZ),
            attendee_count=2,
        )
        self.session.add_all([m_curr1, m_curr2, m_curr3, m_future])
        self.session.commit()

        # Build report
        report1 = build_weekly_report("2026-W40", db=self.session)
        # Test idempotency (run twice -> byte-identical output)
        report2 = build_weekly_report("2026-W40", db=self.session)
        self.assertEqual(report1, report2)

        content = report1.decode("utf-8")
        # Assert summary metrics
        self.assertIn("summary,week,2026-W40", content)
        self.assertIn("summary,meetings,3", content)
        self.assertIn("summary,total_hours,5.50", content)

        # Assert previous week metrics
        self.assertIn("previous_week,week,2026-W39", content)
        self.assertIn("previous_week,meetings,1", content)
        self.assertIn("previous_week,total_hours,1.00", content)

        # Assert changes
        self.assertIn("change,meetings,+2", content)
        self.assertIn("change,meetings_pct,+200.0%", content)
        self.assertIn("change,total_hours,+4.50", content)
        self.assertIn("change,total_hours_pct,+450.0%", content)

        # Assert top meetings order: Long Workshop (3h) -> Sprint Planning (2h) -> Short Standup (0.5h)
        lines = content.splitlines()
        top_lines = [l for l in lines if l.startswith("top_meeting,")]
        self.assertEqual(len(top_lines), 3)
        self.assertIn("Long Workshop", top_lines[0])
        self.assertIn("Sprint Planning", top_lines[1])
        self.assertIn("Short Standup", top_lines[2])


if __name__ == "__main__":
    unittest.main()
