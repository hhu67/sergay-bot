import asyncio
import os
import logging
import sqlite3
import sys
import random
import aiohttp

from dotenv import load_dotenv
from aiogram import Dispatcher, Bot, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class FormNewPhrase(StatesGroup):
    phrase = State()

load_dotenv()
conn = sqlite3.connect("bot.sqlite3")
cursor = conn.cursor()


TGBOT_TOKEN = os.getenv("TGBOT")
if TGBOT_TOKEN is None:
    sys.exit(1)
bot = Bot(token=TGBOT_TOKEN)
dp = Dispatcher()
start_text = """Жми:
/phrase
/new
/view"""

MEDIA_ENDPOINTS = {
    "audio": "https://sergay.hhu67.pw/api/get/audio/random/",
    "photo": "https://sergay.hhu67.pw/api/get/random/",
    "video": "https://sergay.hhu67.pw/api/get/video/random/",
}

# noinspection PyArgumentList
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(start_text)

# noinspection PyArgumentList
@dp.message(Command("phrase"))
async def phrase(message: Message):
    cursor.execute("SELECT phrase FROM sergay_bot ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()

    if not row:
        await message.answer("Записей нет иди нахуй")
        return

    phrase_text = f"серГЕЙ {row[0]}"

    if random.randint(1, 100) <= 50:

        media_type = random.choice(["audio", "photo", "video"])
        api_url = MEDIA_ENDPOINTS[media_type]

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    media_url = data.get("link")

                    if media_type == "audio":
                        await message.answer_audio(audio=media_url, caption=phrase_text)
                    elif media_type == "photo":
                        await message.answer_photo(photo=media_url, caption=phrase_text)
                    elif media_type == "video":
                        await message.answer_video(video=media_url, caption=phrase_text)

            except Exception:

                await message.answer(phrase_text)
    else:
        await message.answer(phrase_text)

# noinspection PyArgumentList
@dp.message(Command("view"))
async def view(message: Message):
    cursor.execute("SELECT * FROM sergay_bot")
    rows = cursor.fetchall()

    if not rows:
        await message.answer("Записей пока нет.")
        return

    view_text = "\n".join(str(row[1]) for row in rows)

    if len(view_text) > 4000:
        for chunk in range(0, len(view_text), 4000):
            await message.answer(view_text[chunk:chunk + 4000])
    else:
        await message.answer(view_text)

# noinspection PyArgumentList
@dp.message(Command("new"))
async def new(message: Message, state: FSMContext):
    await state.set_state(FormNewPhrase.phrase)
    await message.answer("Назови гандона по новому")

@dp.message(FormNewPhrase.phrase)
async def new_insert(message: Message, state: FSMContext):
    user_data = await state.get_data()
    phrase = message.text
    cursor.execute("INSERT INTO sergay_bot (phrase) VALUES (?)", (phrase,))
    conn.commit()
    await state.clear()
    await message.answer(f"Успешно добавленно серГЕЙ {phrase}")

@dp.message(F.text.startswith("/"))
async def all_no_command(message: Message):
    await message.answer("НЕТ")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
