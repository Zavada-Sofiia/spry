from datetime import date
from unittest.mock import MagicMock
import unittest

from app.ai.agenda import (
    AgendaParseError,
    ParsedAgenda,
    cost_usd,
    parse_agenda,
)


class MockUsage:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class MockToolBlock:
    def __init__(self, name: str, tool_input: dict, tool_id: str = "tool_1"):
        self.type = "tool_use"
        self.name = name
        self.id = tool_id
        self.input = tool_input


class MockResponse:
    def __init__(self, content: list, usage: MockUsage, stop_reason: str = "tool_use"):
        self.content = content
        self.usage = usage
        self.stop_reason = stop_reason


class TestAgendaParser(unittest.TestCase):
    def test_valid_tool_call(self):
        client = MagicMock()
        agenda_data = {
            "title": "Pricing Sync",
            "starts_at": "2026-10-19T10:00:00+03:00",
            "duration_minutes": 45,
            "items": [
                {"topic": "New Pro tariffs", "owner": "Olena", "minutes": 15},
                {"topic": "Feedback from clients", "owner": "Taras", "minutes": None},
            ],
            "action_items": [
                {"task": "Collect competitor comparison", "owner": "Taras", "due": "2026-10-23"}
            ],
            "language": "uk",
        }
        client.messages.create.return_value = MockResponse(
            content=[MockToolBlock("record_agenda", agenda_data)],
            usage=MockUsage(120, 80),
        )

        today = date(2026, 10, 19)
        parsed, usage = parse_agenda("Some meeting text", today, "Europe/Kyiv", client=client)

        self.assertIsInstance(parsed, ParsedAgenda)
        self.assertEqual(parsed.title, "Pricing Sync")
        self.assertEqual(len(parsed.items), 2)
        self.assertEqual(parsed.items[0].owner, "Olena")
        self.assertEqual(len(parsed.action_items), 1)
        self.assertEqual(parsed.language, "uk")
        self.assertEqual(usage["input_tokens"], 120)
        self.assertEqual(usage["output_tokens"], 80)
        client.messages.create.assert_called_once()

    def test_missing_tool_call(self):
        client = MagicMock()
        client.messages.create.return_value = MockResponse(
            content=[],
            usage=MockUsage(50, 20),
            stop_reason="end_turn",
        )

        with self.assertRaises(AgendaParseError) as ctx:
            parse_agenda("Hello world", date(2026, 10, 19), "UTC", client=client)

        self.assertIn("no agenda returned (stop_reason=end_turn)", str(ctx.exception))

    def test_invalid_then_valid_retry(self):
        client = MagicMock()
        # First call: missing required 'items' field -> ValidationError
        invalid_data = {
            "title": "Bad Agenda",
            "language": "en",
        }
        # Second call: valid data
        valid_data = {
            "title": "Fixed Agenda",
            "items": [{"topic": "Sprint review", "minutes": 30}],
            "language": "en",
        }
        client.messages.create.side_effect = [
            MockResponse([MockToolBlock("record_agenda", invalid_data, "call_1")], MockUsage(100, 40)),
            MockResponse([MockToolBlock("record_agenda", valid_data, "call_2")], MockUsage(150, 50)),
        ]

        parsed, usage = parse_agenda("Sprint review notes", date(2026, 10, 19), "UTC", client=client)
        self.assertEqual(parsed.title, "Fixed Agenda")
        self.assertEqual(len(parsed.items), 1)
        # Usage must be accumulated across both attempts
        self.assertEqual(usage["input_tokens"], 250)
        self.assertEqual(usage["output_tokens"], 90)
        self.assertEqual(client.messages.create.call_count, 2)

        # Check second call messages include tool_result with is_error=True
        second_call_kwargs = client.messages.create.call_args_list[1][1]
        user_retry_msg = second_call_kwargs["messages"][-1]
        self.assertEqual(user_retry_msg["role"], "user")
        self.assertTrue(user_retry_msg["content"][0]["is_error"])
        self.assertEqual(user_retry_msg["content"][0]["tool_use_id"], "call_1")

    def test_invalid_twice_raises_error(self):
        client = MagicMock()
        invalid_data = {"title": "Bad Agenda"}  # Missing items and language
        client.messages.create.side_effect = [
            MockResponse([MockToolBlock("record_agenda", invalid_data, "call_1")], MockUsage(100, 40)),
            MockResponse([MockToolBlock("record_agenda", invalid_data, "call_2")], MockUsage(120, 40)),
        ]

        with self.assertRaises(AgendaParseError) as ctx:
            parse_agenda("Broken text", date(2026, 10, 19), "UTC", client=client)

        self.assertIn("the model returned an invalid agenda twice", str(ctx.exception))
        self.assertEqual(client.messages.create.call_count, 2)

    def test_cost_usd_calculation(self):
        # Opus 5.5: $4.00/1M in, $20.00/1M out
        # 1,000 in, 500 out -> (1000 * 4 + 500 * 20) / 1,000,000 = (4000 + 10000)/1M = 0.014
        usage = {"input_tokens": 1000, "output_tokens": 500}
        cost = cost_usd("anthropic.claude-opus-5-5", usage)
        self.assertAlmostEqual(cost, 0.014, places=6)

        # Sonnet 5.5: $2.00/1M in, $10.00/1M out
        cost_sonnet = cost_usd("anthropic.claude-sonnet-5-5", usage)
        self.assertAlmostEqual(cost_sonnet, 0.007, places=6)

        # Haiku 5.5: $0.10/1M in, $0.50/1M out
        cost_haiku = cost_usd("anthropic.claude-haiku-5-5", usage)
        self.assertAlmostEqual(cost_haiku, 0.00035, places=6)


if __name__ == "__main__":
    unittest.main()
