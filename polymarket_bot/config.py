from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    allowed_chat_id: int | None


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is missing. Copy env-example.txt to .env and paste your Telegram bot token there."
        )

    allowed_chat_raw = os.getenv("ALLOWED_CHAT_ID", "").strip()
    allowed_chat_id = int(allowed_chat_raw) if allowed_chat_raw else None

    return Settings(
        telegram_bot_token=token,
        allowed_chat_id=allowed_chat_id,
    )
