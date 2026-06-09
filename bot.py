import asyncio
import os
import requests
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
    ReplyKeyboardRemove,
)

TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwS601snzMGKuXdvvJLE4tCVMfUjtTsuORk3T36kBi_ZySCG2E09P4qtFff8R4957x4/exec"
ADMIN_ID = 6287069134
def load_stats():
    try:
        with open("stats.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "users": [],
            "applications": 0,
            "applicants": [],
            "last_applications": []
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

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Оставить заявку")]
    ],
    resize_keyboard=True
)

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📞 Отправить номер",
                request_contact=True
            )
        ]
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
        "👋 Добро пожаловать!\n\n"
        "Оставьте заявку и мы свяжемся с вами в ближайшее время.",
        reply_markup=start_keyboard

    )
    
@dp.message(F.text == "📝 Оставить заявку")
async def start_application(message: Message, state: FSMContext):

    await message.answer(
        "📍 Шаг 1 из 4\n\n"
        "Введите ваше Ф.И.О.",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(Form.fio)

@dp.message(F.text == "/stats")
async def stats_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    stats = load_stats()

    users = len(stats["users"])
    applications = stats["applications"]
    applicants = len(stats["applicants"])

    if users > 0:
        conversion = round(applicants / users * 100, 1)
    else:
        conversion = 0

    await message.answer(
    f"📊 Статистика\n\n"
    f"👥 Посетителей: {users}\n"
    f"📝 Всего заявок: {applications}\n"
    f"🙋 Уникальных заявителей: {applicants}\n"
    f"📈 Конверсия: {conversion}%"
)

@dp.message(Form.fio)
async def get_fio(message: Message, state: FSMContext):

    fio = message.text.strip()

    if len(fio) < 5 or len(fio.split()) < 2:
        await message.answer(
            "❌ Введите корректное Ф.И.О.\n\n"
            "Пример:\n"
            "Иванов Иван Иванович"
        )
        return

    await state.update_data(fio=fio)

    await message.answer(
        "📞 Шаг 2 из 4\n\n"
        "Нажмите кнопку ниже для отправки номера телефона:",
        reply_markup=phone_keyboard
    )

    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def get_phone(message: Message, state: FSMContext):

    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()

        numbers = "".join(filter(str.isdigit, phone))

        if len(numbers) < 10:
            await message.answer(
                "❌ Неверный номер телефона.\n\n"
                "Введите номер ещё раз или нажмите кнопку ниже."
            )
            return

    await state.update_data(phone=phone)

    await message.answer(
        "📧 Шаг 3 из 4\n\nВведите e-mail:",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(Form.email)

@dp.message(Form.email)
async def get_email(message: Message, state: FSMContext):

    email = message.text.strip()

    if "@" not in email or "." not in email:
        await message.answer(
            "❌ Некорректный e-mail.\n\n"
            "Пример:\n"
            "example@mail.ru"
        )
        return

    await state.update_data(email=email)

    await message.answer(
        "💬 Шаг 4 из 4\n\n"
        "Оставьте комментарий:"
    )

    await state.set_state(Form.comment)


@dp.message(Form.comment)
async def get_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)

    data = await state.get_data()

    text = (
        "📋 Проверьте данные\n\n"
        f"👤 {data['fio']}\n"
        f"📞 {data['phone']}\n"
        f"📧 {data['email']}\n"
        f"💬 {data['comment']}\n\n"
        "Все верно?"
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
        "👋 Добро пожаловать!\n\n"
        "Оставьте заявку и мы свяжемся с вами в ближайшее время.\n\n"
        "📍 Шаг 1 из 4\n\n"
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
    
    try:
        requests.post(
            GOOGLE_SCRIPT_URL,
            json={
                "fio": data["fio"],
                "phone": data["phone"],
                "email": data["email"],
                "comment": data["comment"],
                "telegram": username,
                "user_id": message.from_user.id
            },
            timeout=10
        )
    
    except Exception as e:
        print(f"Google Sheets error: {e}")
    
    stats = load_stats()

    stats["applications"] += 1

    user_id = message.from_user.id

    if user_id not in stats["applicants"]:
        stats["applicants"].append(user_id)
        
    stats["last_applications"].append({
        "fio": data["fio"],
        "phone": data["phone"]
    })

    if len(stats["last_applications"]) > 5:
        stats["last_applications"] = stats["last_applications"][-5:]

    save_stats(stats)
    
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
