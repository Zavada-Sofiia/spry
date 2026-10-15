import json
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REPORTS_BUCKET", "test-bucket")

import unittest
from app.reports.lambda_handler import _payload, detect_trigger


class TestLambdaHandlerTriggers(unittest.TestCase):
    def test_direct_invocation(self):
        event = {"week": "2026-W40", "source": "manual"}
        self.assertEqual(_payload(event), event)
        self.assertEqual(detect_trigger(event), "direct")

    def test_direct_schedule_invocation(self):
        event = {"source": "schedule"}
        self.assertEqual(_payload(event), event)
        self.assertEqual(detect_trigger(event), "schedule")

    def test_sqs_schedule_invocation(self):
        event = {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": json.dumps({"source": "schedule", "week": None}),
                }
            ]
        }
        self.assertEqual(_payload(event), {"source": "schedule", "week": None})
        self.assertEqual(detect_trigger(event), "schedule")

    def test_sqs_manual_invocation(self):
        event = {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": json.dumps({"source": "manual", "week": "2026-W39"}),
                }
            ]
        }
        self.assertEqual(_payload(event), {"source": "manual", "week": "2026-W39"})
        self.assertEqual(detect_trigger(event), "sqs")


if __name__ == "__main__":
    unittest.main()
