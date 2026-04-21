# import module
import asyncio
import contextlib
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.types import Update
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from dotenv import load_dotenv, find_dotenv

from core import AI
from logging_config import setup_logging
from memory import MemoryStore

# --------------------
# SETTINGS
# --------------------
# load enviroments
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(find_dotenv())

TOKEN = os.getenv("tg_token")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8080"))
WEBHOOK_DRAIN_TIMEOUT_SECONDS = float(os.getenv("WEBHOOK_DRAIN_TIMEOUT_SECONDS", "15"))
LIMIT_REQUESTS = 10
INACTIVITY_TIMEOUT = timedelta(minutes=10)

user_sessions = {}

setup_logging()
logger = logging.getLogger(__name__)

ai: AI | None = None
memory = MemoryStore()
scheduler_task: asyncio.Task | None = None


# --------------------
# FUNCTIONS
# --------------------

def init_user(user_id: int):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "remaining_requests": LIMIT_REQUESTS,
            "last_active": datetime.now(),
        }


def reset_limits():
    now = datetime.now()
    inactive_users = []

    for user_id, data in user_sessions.items():
        if now - data["last_active"] > INACTIVITY_TIMEOUT:
            inactive_users.append(user_id)

    # delete inactive
    for user_id in inactive_users:
        del user_sessions[user_id]

    # remaining sessions
    for data in user_sessions.values():
        data["remaining_requests"] = LIMIT_REQUESTS


async def scheduler():
    while True:
        await asyncio.sleep(600)
        reset_limits()
        logger.info("Лимиты обновлены.")


def get_webhook_url() -> str:
    if not WEBHOOK_HOST:
        raise RuntimeError("Не задан WEBHOOK_HOST для запуска webhook-режима.")
    return f"{WEBHOOK_HOST.rstrip('/')}{WEBHOOK_PATH}"


def validate_env() -> None:
    missing = []
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not TOKEN:
        missing.append("tg_token")
    if not WEBHOOK_HOST:
        missing.append("WEBHOOK_HOST")

    if missing:
        raise RuntimeError(
            "Не заданы обязательные переменные окружения: "
            f"{', '.join(missing)}."
        )


# --------------------
# HENDLERS
# --------------------

async def start_handler(message: Message):
    user_id = message.from_user.id #type:ignore
    init_user(user_id)

    await message.answer(
        "Привет! Меня зовут Лиза, я консультант компании Atomy 😊\n"
        "Задайте ваш вопрос."
    )


async def text_handler(message: Message):
    user_id = message.from_user.id #type:ignore
    init_user(user_id)

    session = user_sessions[user_id]
    session["last_active"] = datetime.now()

    if session["remaining_requests"] <= 0:
        await message.answer(
            "🚫 Лимит 10 сообщений за 10 минут исчерпан.\n"
            "Попробуйте чуть позже."
        )
        return

    if ai is None:
        logger.error("AI клиент не инициализирован.")
        await message.answer(
            "Сейчас я не могу ответить. Пожалуйста, попробуйте чуть позже."
        )
        return

    async def typing_indicator() -> None:
        while True:
            await message.bot.send_chat_action(message.chat.id, "typing") #type:ignore
            await asyncio.sleep(4)

    typing_task = asyncio.create_task(typing_indicator())

    try:
        history = memory.get_history(user_id)
        answer = await ai.consult(message.text, history=history) #type:ignore

        session["remaining_requests"] -= 1
        await message.answer(answer)
        try:
            memory.add_pair(user_id, message.text, answer) #type:ignore
        except OSError as memory_error:
            logger.exception("Ошибка сохранения памяти: %s", memory_error)

    except Exception as e:
        logger.exception("Ошибка обработки сообщения: %s", e)
        await message.answer(
            "Что-то пошло не так, но я уже стараюсь помочь. Пожалуйста, повторите вопрос чуть позже."
        )
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
        except Exception as typing_error:
            logger.warning(
                "Ошибка typing-индикатора во время cleanup проигнорирована: %s",
                typing_error,
            )


# --------------------
# START
# --------------------

async def main():
    global scheduler_task, ai
    validate_env()
    ai = AI()

    bot = Bot(
        token=TOKEN, #type:ignore
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(text_handler, F.text)

    scheduler_task = asyncio.create_task(scheduler())

    webhook_url = get_webhook_url()
    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
    )
    webhook_info = await bot.get_webhook_info()
    logger.info(
        (
            "Webhook установлен: %s | pending_updates=%s | "
            "last_error_date=%s | last_error_message=%s"
        ),
        webhook_info.url,
        webhook_info.pending_update_count,
        webhook_info.last_error_date,
        webhook_info.last_error_message,
    )

    in_flight_updates: set[asyncio.Task[None]] = set()

    async def process_update(update: Update) -> None:
        try:
            await dp.feed_update(bot, update)
        except Exception:
            logger.exception("Ошибка при асинхронной обработке webhook update.")

    async def webhook_handler(request: web.Request) -> web.Response:
        if WEBHOOK_SECRET:
            secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if secret_header != WEBHOOK_SECRET:
                logger.warning("Отклонён запрос с некорректным webhook secret.")
                return web.Response(status=403, text="Forbidden")

        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        task = asyncio.create_task(process_update(update))
        in_flight_updates.add(task)
        task.add_done_callback(in_flight_updates.discard)
        return web.Response(status=200, text="ok")

    async def health_handler(_: web.Request) -> web.Response:
        return web.Response(status=200, text="ok")

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    app.router.add_get("/health", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=APP_HOST, port=APP_PORT)

    logger.info("Бот запущен в webhook-режиме: http://%s:%s", APP_HOST, APP_PORT)
    await site.start()

    try:
        await asyncio.Event().wait()
    finally:
        await bot.delete_webhook(drop_pending_updates=False)
        await runner.cleanup()

        if in_flight_updates:
            logger.info(
                "Ожидание завершения %s webhook-задач перед остановкой.",
                len(in_flight_updates),
            )
            done, pending = await asyncio.wait(
                in_flight_updates,
                timeout=WEBHOOK_DRAIN_TIMEOUT_SECONDS,
            )
            if pending:
                logger.warning(
                    (
                        "Не удалось дождаться %s webhook-задач за %.1f секунд. "
                        "Задачи будут отменены."
                    ),
                    len(pending),
                    WEBHOOK_DRAIN_TIMEOUT_SECONDS,
                )
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)

            if done:
                await asyncio.gather(*done, return_exceptions=True)

        if scheduler_task:
            scheduler_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await scheduler_task
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
