import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("check_odyssey.py")
SPEC = importlib.util.spec_from_file_location("check_odyssey", MODULE_PATH)
assert SPEC and SPEC.loader
watcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watcher)


class OdysseyWatcherTests(unittest.TestCase):
    def test_filters_odyssey_70mm_imax(self):
        event = {
            "filmId": watcher.MOVIE_ID,
            "attributeIds": ["70-mm"],
            "auditoriumTinyName": "IMAX",
        }
        self.assertTrue(watcher.is_odyssey_70mm_imax(event))
        self.assertFalse(watcher.is_odyssey_70mm_imax({**event, "filmId": "other"}))

    def test_best_event_ignores_known_zero_seats(self):
        sold_out = {
            "eventDateTime": "2026-09-14T20:00:00",
            "availabilityRatio": 0.0156,
        }
        available = {
            "eventDateTime": "2026-09-14T20:30:00",
            "availabilityRatio": 0.0234,
        }
        self.assertIs(watcher.get_best_event([sold_out, available]), available)

    def test_100_to_200_basis_points_means_zero_seats(self):
        for ratio in (0.0100, 0.0156, 0.0182, 0.0200):
            with self.subTest(ratio=ratio):
                event = {"availabilityRatio": ratio}
                self.assertEqual(watcher.get_seat_count(event), 0)
                self.assertEqual(watcher.status_text(event), "❌ 0 seats")

    def test_target_notification_is_deduplicated(self):
        event = {
            "id": 123,
            "eventDateTime": "2026-09-14T20:00:00",
            "availabilityRatio": 0.0234,
            "bookingLink": "https://example.com/book",
        }
        state = watcher.default_state()
        with patch.object(watcher, "notify") as notify:
            watcher.handle_target_date("2026-09-14", [event], state)
            watcher.handle_target_date("2026-09-14", [event], state)
        notify.assert_called_once()
        self.assertEqual(state["target_notifications"], ["2026-09-14-123"])

    def test_slack_api_requires_token(self):
        with patch.object(watcher, "SLACK_BOT_TOKEN", ""):
            with self.assertRaisesRegex(RuntimeError, "SLACK_BOT_TOKEN"):
                watcher.slack_api("chat.postMessage", {"channel": "U123", "text": "test"})


if __name__ == "__main__":
    unittest.main()
