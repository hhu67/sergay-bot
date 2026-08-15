import asyncio
import os
import logging
import sqlite3
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
bot = Bot(token=TGBOT_TOKEN)
dp = Dispatcher()
start_text = """Жми:
/phrase
/new"""

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(start_text)

@dp.message(Command("phrase"))
async def phrase(message: Message):
    cursor.execute("SELECT phrase FROM sergay_bot ORDER BY RANDOM() LIMIT 1")
    phrase = cursor.fetchone()[0]
    await message.answer(f"серГЕЙ {phrase}")

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
