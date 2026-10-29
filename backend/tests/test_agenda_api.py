import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestAgendaAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)

    def test_create_agenda_without_suggestion(self):
        payload = {
            "title": "Manual Team Sync",
            "duration_minutes": 30,
            "items": [
                {"topic": "Project status", "owner": "Alice", "minutes": 15},
                {"topic": "Blockers", "owner": "Bob", "minutes": 15},
            ],
            "action_items": [
                {"task": "Prepare slide deck", "owner": "Alice", "due": "2026-11-01"}
            ],
            "language": "en",
        }
        res = self.client.post("/api/agendas", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["title"], "Manual Team Sync")
        self.assertIsNone(data["ai_suggestion"])
        self.assertIsNone(data["model"])
        self.assertIsNone(data["prompt_version"])
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(len(data["action_items"]), 1)

    def test_create_agenda_with_ai_suggestion(self):
        ai_suggestion = {
            "title": "Suggested Sync",
            "starts_at": "2026-10-20T10:00:00Z",
            "duration_minutes": 45,
            "items": [
                {"topic": "Tariffs Pro", "owner": "Olena", "minutes": 15},
                {"topic": "Feedback", "owner": "Taras", "minutes": None},
            ],
            "action_items": [
                {"task": "Competitor matrix", "owner": "Taras", "due": "2026-10-24"}
            ],
            "language": "uk",
        }
        payload = {
            "title": "Final Pricing Sync",  # user edited title
            "duration_minutes": 45,
            "items": [
                {"topic": "Tariffs Pro", "owner": "Olena", "minutes": 15},
                {"topic": "Customer Feedback", "owner": "Taras", "minutes": 20},  # user edited
            ],
            "action_items": [
                {"task": "Competitor matrix", "owner": "Taras", "due": "2026-10-24"}
            ],
            "language": "uk",
            "ai_suggestion": ai_suggestion,
            "model": "anthropic.claude-opus-5-5",
            "prompt_version": "agenda-v1",
        }
        res = self.client.post("/api/agendas", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["title"], "Final Pricing Sync")
        self.assertEqual(data["model"], "anthropic.claude-opus-5-5")
        self.assertEqual(data["prompt_version"], "agenda-v1")
        self.assertIsNotNone(data["ai_suggestion"])
        self.assertEqual(data["ai_suggestion"]["title"], "Suggested Sync")
        self.assertEqual(data["items"][1]["topic"], "Customer Feedback")

    def test_get_agendas(self):
        res = self.client.get("/api/agendas")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 2)


if __name__ == "__main__":
    unittest.main()
