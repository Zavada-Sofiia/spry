from datetime import date
import json
from unittest.mock import MagicMock, patch
import unittest

from app.ai.agenda import AgendaParseError, ParsedAgenda
from app.ai.agenda_lambda import handler


class TestAgendaLambda(unittest.TestCase):
    def test_missing_auth_header_returns_401(self):
        event = {"headers": {}, "body": json.dumps({"text": "Meeting notes"})}
        resp = handler(event)
        self.assertEqual(resp["statusCode"], 401)
        data = json.loads(resp["body"])
        self.assertIn("error", data)

    @patch("app.ai.agenda_lambda.verify_token")
    def test_invalid_token_returns_401(self, mock_verify):
        mock_verify.side_effect = Exception("Invalid signature")
        event = {
            "headers": {"authorization": "Bearer badtoken"},
            "body": json.dumps({"text": "Meeting notes"}),
        }
        resp = handler(event)
        self.assertEqual(resp["statusCode"], 401)
        data = json.loads(resp["body"])
        self.assertIn("Unauthorized", data["error"])

    @patch("app.ai.agenda_lambda.verify_token")
    @patch("app.ai.agenda_lambda.parse_agenda")
    def test_oversize_text_returns_413_without_calling_model(self, mock_parse, mock_verify):
        mock_verify.return_value = "user-123"
        huge_text = "a" * 10001
        event = {
            "headers": {"authorization": "Bearer validtoken"},
            "body": json.dumps({"text": huge_text}),
        }
        resp = handler(event)
        self.assertEqual(resp["statusCode"], 413)
        mock_parse.assert_not_called()

    @patch("app.ai.agenda_lambda.verify_token")
    @patch("app.ai.agenda_lambda.parse_agenda")
    def test_parse_error_returns_422(self, mock_parse, mock_verify):
        mock_verify.return_value = "user-123"
        mock_parse.side_effect = AgendaParseError("the model returned an invalid agenda twice")
        event = {
            "headers": {"authorization": "Bearer validtoken"},
            "body": json.dumps({"text": "Garbage text", "today": "2026-10-19", "tz": "UTC"}),
        }
        resp = handler(event)
        self.assertEqual(resp["statusCode"], 422)
        data = json.loads(resp["body"])
        self.assertIn("invalid agenda twice", data["error"])

    @patch("app.ai.agenda_lambda.verify_token")
    @patch("app.ai.agenda_lambda.parse_agenda")
    def test_throttling_returns_429(self, mock_parse, mock_verify):
        mock_verify.return_value = "user-123"
        mock_parse.side_effect = Exception("ThrottlingException: Too many requests")
        event = {
            "headers": {"authorization": "Bearer validtoken"},
            "body": json.dumps({"text": "Valid text", "today": "2026-10-19", "tz": "UTC"}),
        }
        resp = handler(event)
        self.assertEqual(resp["statusCode"], 429)
        data = json.loads(resp["body"])
        self.assertIn("Service busy", data["error"])

    @patch("app.ai.agenda_lambda.logger.info")
    @patch("app.ai.agenda_lambda.verify_token")
    @patch("app.ai.agenda_lambda.parse_agenda")
    def test_success_returns_200_and_logs_structured_line(self, mock_parse, mock_verify, mock_log):
        mock_verify.return_value = "user-456"
        mock_agenda = ParsedAgenda(
            title="Design Review",
            items=[{"topic": "Mockups", "minutes": 20}],
            language="en",
        )
        mock_usage = {"input_tokens": 100, "output_tokens": 50}
        mock_parse.return_value = (mock_agenda, mock_usage)

        event = {
            "headers": {"authorization": "Bearer validtoken"},
            "body": json.dumps({"text": "Review mockups for 20m", "today": "2026-10-19", "tz": "Europe/Kyiv"}),
        }
        resp = handler(event)
        self.assertEqual(resp["statusCode"], 200)
        data = json.loads(resp["body"])
        self.assertEqual(data["agenda"]["title"], "Design Review")
        self.assertEqual(data["prompt_version"], "agenda-v1")
        self.assertIn("model", data)

        # Check structured log
        mock_log.assert_called_once()
        log_line = json.loads(mock_log.call_args[0][0])
        self.assertEqual(log_line["event"], "agenda_parsed")
        self.assertEqual(log_line["user"], "user-456")
        self.assertEqual(log_line["prompt_version"], "agenda-v1")
        self.assertEqual(log_line["input_tokens"], 100)
        self.assertEqual(log_line["output_tokens"], 50)
        self.assertIn("latency_ms", log_line)
        self.assertIn("cost_usd", log_line)


if __name__ == "__main__":
    unittest.main()
