# import module
import asyncio
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from dotenv import load_dotenv

from core import AI
from memory import MemoryStore

# --------------------
# SETTINGS
# --------------------
# load enviroments
load_dotenv()

TOKEN = os.getenv("tg_token")

LIMIT_REQUESTS = 10
INACTIVITY_TIMEOUT = timedelta(minutes=10)

user_sessions = {}

ai = AI()
memory = MemoryStore()


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
        print("Лимиты обновлены.")


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

    await message.bot.send_chat_action(message.chat.id, "typing") #type:ignore

    try:
        history = memory.get_history(user_id)
        answer = await ai.consult(message.text, history=history) #type:ignore

        session["remaining_requests"] -= 1
        memory.add_pair(user_id, message.text, answer) #type:ignore

        await message.answer(answer)

    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("Произошла ошибка при обработке запроса.")


# --------------------
# START
# --------------------

async def main():
    bot = Bot(
        token=TOKEN, #type:ignore
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(text_handler, F.text)

    asyncio.create_task(scheduler())

    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
