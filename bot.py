import asyncio
import os
import json
from flask import Flask
import threading
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6287069134
def load_stats():
    try:
        with open("stats.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "users": [],
            "applications": 0
        }

def save_stats(stats):
    with open("stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f)


class Form(StatesGroup):
    fio = State()
    phone = State()
    email = State()
    comment = State()
    confirm = State()


dp = Dispatcher(storage=MemoryStorage())


confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Подтвердить")],
        [KeyboardButton(text="❌ Заполнить заново")]
    ],
    resize_keyboard=True
)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
        
    stats = load_stats()

    user_id = message.from_user.id

    if user_id not in stats["users"]:
        stats["users"].append(user_id)
        save_stats(stats)
        
    await state.clear()

    await message.answer(
        "Здравствуйте! Пожалуйста, заполните заявку.\n\n"
        "Введите ваше Ф.И.О."
    )

    await state.set_state(Form.fio)


@dp.message(Form.fio)
async def get_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)

    await message.answer("Введите номер телефона:")
    await state.set_state(Form.phone)


@dp.message(Form.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)

    await message.answer("Введите e-mail:")
    await state.set_state(Form.email)


@dp.message(Form.email)
async def get_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)

    await message.answer("Оставьте комментарий:")
    await state.set_state(Form.comment)


@dp.message(Form.comment)
async def get_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)

    data = await state.get_data()

    text = (
        "Проверьте данные:\n\n"
        f"👤 Ф.И.О.: {data['fio']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📧 E-mail: {data['email']}\n"
        f"💬 Комментарий: {data['comment']}\n\n"
        "Подтвердить заявку?"
    )

    await message.answer(
        text,
        reply_markup=confirm_keyboard
    )

    await state.set_state(Form.confirm)


@dp.message(Form.confirm, F.text == "❌ Заполнить заново")
async def restart_form(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Введите ваше Ф.И.О.",
        reply_markup=None
    )

    await state.set_state(Form.fio)

@dp.message(F.text == "❌ Заполнить заново")
async def restart_anytime(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Введите ваше Ф.И.О.",
        reply_markup=None
    )

    await state.set_state(Form.fio)


@dp.message(Form.confirm, F.text == "✅ Подтвердить")
async def confirm_form(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "не указан"
    )

    application = (
        "📥 Новая заявка\n\n"
        f"👤 Ф.И.О.: {data['fio']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📧 E-mail: {data['email']}\n"
        f"💬 Комментарий: {data['comment']}\n\n"
        f"Telegram: {username}\n"
        f"ID: {message.from_user.id}"
    )

    await bot.send_message(
        ADMIN_ID,
        application
    )

    await message.answer(
        "✅ Спасибо! Ваша заявка успешно отправлена.",
        reply_markup=None
    )

    await state.clear()


app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
async def main():
    bot = Bot(TOKEN)

    await dp.start_polling(bot)


if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    asyncio.run(main())
