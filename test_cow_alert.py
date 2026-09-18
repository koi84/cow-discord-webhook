import unittest
from datetime import datetime, timedelta, timezone

from cow_alert import GAME_RE, wanted


class CowAlertTests(unittest.TestCase):
    def test_parse_game(self):
        text = (
            "10909461 : scrap date: 13-09-2026 08:20:01, server: IT🇮🇹 - "
            "game day: 1, Scenario: Clash of Nations [x24]. "
            "Start Date: 13-09-2026 08:15:19. Opens Slots: 19."
        )
        game = GAME_RE.search(text).groupdict()
        self.assertEqual(game["id"], "10909461")
        self.assertEqual(game["language"], "IT")
        self.assertEqual(game["scenario"], "Clash of Nations [x24]")
        self.assertEqual(game["slots"], "19")

    def test_filters(self):
        fresh_start = (datetime.now(timezone.utc) - timedelta(minutes=3)).strftime(
            "%d-%m-%Y %H:%M:%S"
        )
        config = {
            "scenarios": ["World at War [x4]"],
            "languages": ["FR", "EN", "DE", "IT"],
            "only_open_games": True,
            "max_start_age_minutes": 10,
        }
        self.assertTrue(wanted(
            {"scenario": "World at War [x4]", "language": "DE", "slots": 42,
             "start": fresh_start},
            config,
        ))
        self.assertFalse(wanted(
            {"scenario": "World at War [x4]", "language": "ES", "slots": 42,
             "start": fresh_start},
            config,
        ))
        self.assertFalse(wanted(
            {"scenario": "World at War [x4]", "language": "FR", "slots": 0,
             "start": fresh_start},
            config,
        ))

    def test_old_game_is_ignored(self):
        old_start = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime(
            "%d-%m-%Y %H:%M:%S"
        )
        config = {
            "scenarios": ["World at War [x1]"],
            "languages": ["FR"],
            "only_open_games": True,
            "max_start_age_minutes": 10,
        }
        self.assertFalse(wanted(
            {"scenario": "World at War [x1]", "language": "FR", "slots": 80,
             "start": old_start},
            config,
        ))


if __name__ == "__main__":
    unittest.main()
