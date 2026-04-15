from __future__ import annotations

from typing import Any

import httpx

from polymarket_bot.scanner import choose_yes_token_id


class PolymarketClient:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._timeout = httpx.Timeout(timeout_seconds)
        self._gamma_base_url = "https://gamma-api.polymarket.com"
        self._clob_base_url = "https://clob.polymarket.com"

    async def _get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            return response.json()

    async def _post_json(self, url: str, payload: Any) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    async def get_tag_by_slug(self, slug: str) -> dict[str, Any]:
        data = await self._get_json(f"{self._gamma_base_url}/tags/slug/{slug}")
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected tag response for slug '{slug}'.")
        return data

    async def list_active_events_for_tag(self, tag_slug: str, tag_id: str | int) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        offset = 0
        limit = 100

        while True:
            page = await self._get_json(
                f"{self._gamma_base_url}/events",
                params={
                    "tag_slug": tag_slug,
                    "tag_id": tag_id,
                    "active": "true",
                    "closed": "false",
                    "archived": "false",
                    "related_tags": "false",
                    "limit": str(limit),
                    "offset": str(offset),
                },
            )
            if not isinstance(page, list):
                raise ValueError("Unexpected events response from Polymarket.")

            events.extend(item for item in page if isinstance(item, dict))
            if len(page) < limit:
                break
            offset += limit

        return events

    async def get_orderbooks_for_events(self, events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        token_ids: list[str] = []
        for event in events:
            markets = event.get("markets") or []
            if not isinstance(markets, list):
                continue
            for market in markets:
                if not isinstance(market, dict):
                    continue
                if market.get("bestAsk") is not None:
                    continue
                token_id = choose_yes_token_id(market)
                if token_id:
                    token_ids.append(token_id)

        unique_token_ids = list(dict.fromkeys(token_ids))
        if not unique_token_ids:
            return {}

        books: dict[str, dict[str, Any]] = {}
        chunk_size = 50
        for start in range(0, len(unique_token_ids), chunk_size):
            chunk = unique_token_ids[start : start + chunk_size]
            payload = [{"token_id": token_id} for token_id in chunk]
            page = await self._post_json(f"{self._clob_base_url}/books", payload)
            if not isinstance(page, list):
                raise ValueError("Unexpected order books response from Polymarket.")
            for item in page:
                if not isinstance(item, dict):
                    continue
                asset_id = str(item.get("asset_id") or "")
                if asset_id:
                    books[asset_id] = item

        return books
