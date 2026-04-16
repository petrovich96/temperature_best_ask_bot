from __future__ import annotations

import asyncio
import unittest
from decimal import Decimal
from unittest.mock import AsyncMock

from polymarket_bot.scanner import choose_yes_token_id, format_scan_results, scan_event
from polymarket_bot.telegram_bot import MAX_RESULTS, scan_temperature_markets


class ScannerTests(unittest.TestCase):
    def test_choose_yes_token_id_from_outcomes(self) -> None:
        market = {
            "clobTokenIds": '["token-no", "token-yes"]',
            "outcomes": '["No", "Yes"]',
        }

        self.assertEqual(choose_yes_token_id(market), "token-yes")

    def test_scan_event_uses_best_ask_from_market_when_present(self) -> None:
        event = {
            "id": "event-1",
            "title": "Rainfall in Kyiv",
            "slug": "rainfall-in-kyiv",
            "markets": [
                {
                    "id": "m1",
                    "question": "0-5 mm",
                    "active": True,
                    "closed": False,
                    "bestAsk": "0.45",
                },
                {
                    "id": "m2",
                    "question": "5-10 mm",
                    "active": True,
                    "closed": False,
                    "bestAsk": "0.60",
                },
            ],
        }

        result = scan_event(event, orderbooks_by_token_id={})

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.total_best_ask, Decimal("1.05"))

    def test_scan_event_falls_back_to_orderbook(self) -> None:
        event = {
            "id": "event-2",
            "title": "Rainfall in Odesa",
            "slug": "rainfall-in-odesa",
            "markets": [
                {
                    "id": "m1",
                    "question": "0-5 mm",
                    "active": True,
                    "closed": False,
                    "bestAsk": None,
                    "clobTokenIds": '["yes-token", "no-token"]',
                    "outcomes": '["Yes", "No"]',
                },
                {
                    "id": "m2",
                    "question": "5-10 mm",
                    "active": True,
                    "closed": False,
                    "bestAsk": "0.55",
                },
            ],
        }
        orderbooks = {
            "yes-token": {
                "asset_id": "yes-token",
                "asks": [{"price": "0.52", "size": "100"}],
            }
        }

        result = scan_event(event, orderbooks_by_token_id=orderbooks)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.total_best_ask, Decimal("1.07"))
        self.assertEqual(result.basket_prices[0].best_ask_source, "clob.books")

    def test_format_scan_results_empty(self) -> None:
        text = format_scan_results([])
        self.assertIn("Temperature", text)
        self.assertIn("best ask", text)

    def test_scan_temperature_markets_returns_only_first_ten_results(self) -> None:
        events = [
            {
                "id": f"event-{index}",
                "title": f"Event {index}",
                "slug": f"event-{index}",
                "markets": [
                    {
                        "id": f"m-{index}",
                        "question": f"Question {index}",
                        "active": True,
                        "closed": False,
                        "bestAsk": f"{Decimal('1.50') - (Decimal('0.01') * index)}",
                    }
                ],
            }
            for index in range(12)
        ]

        client = AsyncMock()
        client.get_tag_by_slug.return_value = {"id": "temperature-tag"}
        client.list_active_events_for_tag.return_value = events
        client.get_orderbooks_for_events.return_value = {}

        results = asyncio.run(scan_temperature_markets(client))

        self.assertEqual(len(results), MAX_RESULTS)
        self.assertEqual(results[0].event_id, "event-0")
        self.assertEqual(results[-1].event_id, "event-9")


if __name__ == "__main__":
    unittest.main()
