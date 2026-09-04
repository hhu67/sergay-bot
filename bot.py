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
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class FormNewPhrase(StatesGroup):
    phrase = State()

class FormAnswerForQ(StatesGroup):
    answ = State()

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
/view
/instruction_gift
/try_gift"""

inst_text = """Инструкция для подарка
Первое возраст пидора

Второе расположите по порядку маленькие буквы на русском
а) НейроГЕЙ @Sergey_ai_gptbot
б) Сайт(именно новый) https://sergay.hhu67.pw
в) Страшно боюс боюс бот @Sergayuuibot
г) Унижение @Sergay_uubot

Третье любимый домен сергея(именно существующей) то есть домены формата .пидор не подойдут

В итоге должен получится ответ формата 99абвг.домен
"""

MEDIA_ENDPOINTS = {
    "audio": "https://sergay.hhu67.pw/api/get/audio/random/",
    "photo": "https://sergay.hhu67.pw/api/get/random/",
    "video": "https://sergay.hhu67.pw/api/get/video/random/",
}

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(start_text)

@dp.message(Command("phrase"))
async def phrase(message: Message):
    cursor.execute("SELECT phrase FROM sergay_bot ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()

    if not row:
        await message.answer("Записей нет иди нахуй")
        return

    phrase_text = row[0]

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

@dp.message(Command("try_gift"))
async def try_gift_h(message: Message, state: FSMContext):
    await state.set_state(FormAnswerForQ.answ)
    await message.answer("Давай попробуй")

# ИСПРАВЛЕНО: startswith вместо startswitch
@dp.message(FormAnswerForQ.answ, ~F.text.startswith("/"))
async def try_gift_t(message: Message, state: FSMContext):
    user_id = message.from_user.id
    answer = message.text.strip().lower()

    if answer != "67гавб.gay":
        await message.answer("Не верно пошел нахуй")
        # Очищаем состояние или оставляем для повторной попытки
        return

    await state.clear()
    await message.answer("Правильно! Отправляю подарок...")

    try:
        # 1. Получаем список доступных подарков
        gifts_data = await bot.get_available_gifts()
        
        # 2. Ищем подарок со стоимостью ровно 50 звёзд
        target_gift = next(
            (g for g in gifts_data.gifts if g.star_count == 50 and (g.remaining_count is None or g.remaining_count > 0)),
            None
        )
        
        if not target_gift:
            await message.answer("Ошибка: подарок за 50 звёзд сейчас недоступен в Telegram.")
            return

        # 3. Отправляем подарок пользователю
        await bot.send_gift(
            user_id=user_id,
            gift_id=target_gift.id,
            text="Держи подарок за 50 звёзд! 🎉"
        )
        await message.answer("🎉 Подарок за 50 звёзд отправлен в твой профиль!")

    except Exception as e:
        logging.error(f"Ошибка при отправке подарка: {e}")
        await message.answer(f"Не удалось выдать подарок: {e}")

@dp.message(Command("instruction_gift"))
async def inst_for_try_gift(message: Message):
    await message.answer(inst_text)

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

@dp.message(Command("new"))
async def new(message: Message, state: FSMContext):
    await state.set_state(FormNewPhrase.phrase)
    await message.answer("Назови гандона по новому или отмени через /cancel")

@dp.message(Command("cancel"), StateFilter("*"))
async def cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Сергей отменил ваше действие")

@dp.message(FormNewPhrase.phrase, ~F.text.startswith("/"))
async def new_insert(message: Message, state: FSMContext):
    phrase = message.text
    cursor.execute("INSERT INTO sergay_bot (phrase) VALUES (?)", (phrase,))
    conn.commit()
    await state.clear()
    await message.answer(f"Успешно добавленно {phrase}")

@dp.message(F.text.startswith("/"))
async def all_no_command(message: Message):
    await message.answer("НЕТ")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())