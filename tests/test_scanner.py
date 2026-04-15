from __future__ import annotations

import unittest
from decimal import Decimal

from polymarket_bot.scanner import choose_yes_token_id, format_scan_results, scan_event


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
        self.assertIn("не знайдено", text)


if __name__ == "__main__":
    unittest.main()
