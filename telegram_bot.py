from __future__ import annotations

import logging
from decimal import Decimal

import httpx
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes

from polymarket_bot.config import Settings, load_settings
from polymarket_bot.polymarket import PolymarketClient
from polymarket_bot.scanner import EventScanResult, format_scan_results, scan_event


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
TELEGRAM_MESSAGE_LIMIT = 4000
MAX_RESULTS = 10


def is_allowed_chat(settings: Settings, chat_id: int) -> bool:
    return settings.allowed_chat_id is None or settings.allowed_chat_id == chat_id


async def reject_if_not_allowed(update: Update, settings: Settings) -> bool:
    chat = update.effective_chat
    if chat is None:
        return True

    if is_allowed_chat(settings, chat.id):
        return False

    if update.effective_message:
        await update.effective_message.reply_text("Цей бот налаштований лише для одного дозволеного чату.")
    return True


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if await reject_if_not_allowed(update, settings):
        return

    message = (
        "Це бот для перевірки ринків Polymarket у категорії Temperature.\n\n"
        "Команди:\n"
        "/help - коротка підказка\n"
        "/scan - перевірити картки, де сума best ask усіх кошиків більша за 100¢"
    )
    if update.effective_message:
        await update.effective_message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if await reject_if_not_allowed(update, settings):
        return

    message = (
        "Як користуватися ботом:\n"
        "1. Напишіть /scan\n"
        "2. Зачекайте кілька секунд\n"
        "3. Отримаєте список карток, якщо знайдено суму понад 100¢\n\n"
        "Якщо список порожній, бот так і напише."
    )
    if update.effective_message:
        await update.effective_message.reply_text(message)


async def scan_temperature_markets(client: PolymarketClient) -> list[EventScanResult]:
    tag = await client.get_tag_by_slug("temperature")
    tag_id = tag.get("id")
    if tag_id is None:
        raise ValueError("Polymarket did not return a tag id for 'temperature'.")

    events = await client.list_active_events_for_tag("temperature", tag_id)
    orderbooks = await client.get_orderbooks_for_events(events)

    results: list[EventScanResult] = []
    for event in events:
        result = scan_event(event, orderbooks_by_token_id=orderbooks, threshold=Decimal("1.00"))
        if result:
            results.append(result)

    results.sort(key=lambda item: item.total_best_ask, reverse=True)
    return results[:MAX_RESULTS]


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    client: PolymarketClient = context.application.bot_data["polymarket_client"]

    if await reject_if_not_allowed(update, settings):
        return

    if update.effective_chat:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    if update.effective_message:
        await update.effective_message.reply_text("Перевіряю активні ринки Temperature у Polymarket...")

    try:
        results = await scan_temperature_markets(client)
        text = format_scan_results(results)
    except (httpx.HTTPError, ValueError) as exc:
        logger.exception("Scan failed")
        text = (
            "Не вдалося отримати дані з Polymarket прямо зараз. "
            "Спробуйте ще раз трохи пізніше.\n\n"
            f"Деталь: {exc}"
        )

    if update.effective_message:
        for chunk in split_message(text):
            await update.effective_message.reply_text(chunk, disable_web_page_preview=True)


def split_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n\n", 0, limit)
        if cut <= 0:
            cut = remaining.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()

    if remaining:
        chunks.append(remaining)
    return chunks


def build_application(settings: Settings) -> Application:
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["settings"] = settings
    application.bot_data["polymarket_client"] = PolymarketClient()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("scan", scan_command))

    return application


def main() -> None:
    settings = load_settings()
    application = build_application(settings)
    application.run_polling(drop_pending_updates=True)
