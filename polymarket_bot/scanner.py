from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


DecimalLike = Decimal | int | float | str


@dataclass(slots=True)
class BasketPrice:
    market_id: str
    question: str
    best_ask: Decimal
    best_ask_source: str


@dataclass(slots=True)
class EventScanResult:
    event_id: str
    title: str
    slug: str
    url: str
    basket_prices: list[BasketPrice]

    @property
    def total_best_ask(self) -> Decimal:
        return sum((basket.best_ask for basket in self.basket_prices), start=Decimal("0"))


def to_decimal(value: DecimalLike | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned or cleaned.lower() == "null":
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
    return None


def parse_jsonish_list(raw_value: Any) -> list[Any]:
    if isinstance(raw_value, list):
        return raw_value
    if not isinstance(raw_value, str):
        return []

    text = raw_value.strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []

    return parsed if isinstance(parsed, list) else []


def choose_yes_token_id(market: dict[str, Any]) -> str | None:
    token_ids = parse_jsonish_list(market.get("clobTokenIds"))
    outcomes = parse_jsonish_list(market.get("outcomes"))

    if not token_ids:
        return None

    if outcomes:
        for index, outcome in enumerate(outcomes):
            if str(outcome).strip().lower() == "yes" and index < len(token_ids):
                return str(token_ids[index])

    return str(token_ids[0])


def build_market_url(event: dict[str, Any], market: dict[str, Any] | None = None) -> str:
    event_slug = str(event.get("slug") or "").strip()
    market_slug = str((market or {}).get("slug") or "").strip()

    if event_slug:
        return f"https://polymarket.com/event/{event_slug}"
    if market_slug:
        return f"https://polymarket.com/market/{market_slug}"
    return "https://polymarket.com/weather/temperature"


def scan_event(
    event: dict[str, Any],
    orderbooks_by_token_id: dict[str, dict[str, Any]],
    threshold: Decimal = Decimal("1.00"),
) -> EventScanResult | None:
    markets = event.get("markets") or []
    if not isinstance(markets, list):
        return None

    basket_prices: list[BasketPrice] = []
    for market in markets:
        if not isinstance(market, dict):
            continue
        if not market.get("active") or market.get("closed"):
            continue

        market_id = str(market.get("id") or "")
        question = str(market.get("question") or market.get("groupItemTitle") or "Untitled market")

        best_ask = to_decimal(market.get("bestAsk"))
        source = "market.bestAsk"

        if best_ask is None:
            token_id = choose_yes_token_id(market)
            if token_id:
                orderbook = orderbooks_by_token_id.get(token_id)
                asks = (orderbook or {}).get("asks") or []
                if asks and isinstance(asks, list):
                    best_ask = to_decimal(asks[0].get("price"))
                    source = "clob.books"

        if best_ask is None:
            continue

        basket_prices.append(
            BasketPrice(
                market_id=market_id,
                question=question,
                best_ask=best_ask,
                best_ask_source=source,
            )
        )

    if not basket_prices:
        return None

    result = EventScanResult(
        event_id=str(event.get("id") or ""),
        title=str(event.get("title") or "Untitled event"),
        slug=str(event.get("slug") or ""),
        url=build_market_url(event),
        basket_prices=basket_prices,
    )

    if result.total_best_ask <= threshold:
        return None

    return result


def format_scan_results(results: list[EventScanResult]) -> str:
    if not results:
        return (
            "Зараз у категорії Temperature не знайдено карток, "
            "де сума best ask усіх кошиків більша за 100¢."
        )

    parts = ["Знайдено картки у Temperature, де сума best ask перевищує 100¢:\n"]
    for index, result in enumerate(results, start=1):
        total_cents = (result.total_best_ask * Decimal("100")).quantize(Decimal("0.01"))
        basket_lines = []
        for basket in result.basket_prices:
            cents = (basket.best_ask * Decimal("100")).quantize(Decimal("0.01"))
            basket_lines.append(f"• {basket.question}: {cents}¢")

        parts.append(
            f"{index}. {result.title}\n"
            f"Сума: {total_cents}¢\n"
            + "\n".join(basket_lines)
            + f"\nПосилання: {result.url}"
        )

    return "\n\n".join(parts)
