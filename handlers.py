# handlers.py
import os
import time
import asyncio
import random
import string
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from PIL import Image, ImageFilter

from function import *
from fsm_states import UserStates
from runpod.call_runpod import call_runpod_api
from payments_stars import router as payments_router, CREDIT_PACKAGES
from logs import log_message
from payments_crypto import register_crypto_handlers

TEST_MODE = os.getenv("TEST_MODE", "True") == "True"

# -------------------
# KEYBOARDS
# -------------------
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📸 Send photo"), KeyboardButton(text="💳 Buy credits")],
        [KeyboardButton(text="🌐 Language"), KeyboardButton(text="🛠 Support")]
    ],
    resize_keyboard=True
)

send_photo_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Back to menu")]],
    resize_keyboard=True
)

# Кнопки покупки кредитов через Crypto с отдельными Show credits
crypto_credits_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 Buy credits"), KeyboardButton(text="💰 Show my credits")],
        [KeyboardButton(text="⬅️ Back to menu")]
    ],
    resize_keyboard=True
)

def buy_credits_keyboard():
    keyboard = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    for pkg_id, pkg in CREDIT_PACKAGES.items():
        keyboard.add(KeyboardButton(text=pkg["name"]))
    keyboard.add(KeyboardButton(text="⬅️ Back to menu"))
    return keyboard

def get_user_agreement_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ I agree (20 free credits)", callback_data="agree")]
        ]
    )

# -------------------
# USER AGREEMENT
# -------------------
AGREED_USERS_FILE = "agreed_users.json"
user_agreed = set()

def load_agreed_users():
    global user_agreed
    try:
        with open(AGREED_USERS_FILE, "r", encoding="utf-8") as f:
            user_agreed = set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        user_agreed = set()
    return user_agreed

def save_agreed_users(users_set):
    with open(AGREED_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(users_set), f, ensure_ascii=False, indent=2)

def is_user_agreed(user_id: int) -> bool:
    return user_id in user_agreed

# -------------------
# CREDITS SYSTEM
# -------------------
CREDITS_FILE = "credits.json"

def load_credits():
    if not os.path.exists(CREDITS_FILE):
        return {}
    try:
        with open(CREDITS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_credits(credits_dict):
    with open(CREDITS_FILE, "w", encoding="utf-8") as f:
        json.dump(credits_dict, f, ensure_ascii=False, indent=2)

credits = load_credits()

def get_user_credits(user_id: int) -> int:
    return credits.get(str(user_id), 0)

def add_credits(user_id: int, amount: int):
    uid = str(user_id)
    credits[uid] = credits.get(uid, 0) + amount
    save_credits(credits)

def spend_credits(user_id: int, amount: int) -> bool:
    uid = str(user_id)
    current = credits.get(uid, 0)
    if current >= amount:
        credits[uid] = current - amount
        save_credits(credits)
        return True
    return False

# -------------------
# PHOTO HANDLING
# -------------------
async def save_photo(message, bot):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)

    random_letters = ''.join(random.choices(string.ascii_lowercase, k=10))
    filename = f"{message.from_user.id}_{random_letters}.jpg"

    folder = "photos"
    await asyncio.to_thread(os.makedirs, folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    def write_file():
        with open(filepath, "wb") as f:
            f.write(downloaded_file.read())

    await asyncio.to_thread(write_file)
    return filepath

async def blur_image(filepath: str) -> str:
    def _blur_sync(path):
        image = Image.open(path)
        blurred = image.filter(ImageFilter.GaussianBlur(radius=25))
        folder, original_filename = os.path.split(path)
        base, ext = os.path.splitext(original_filename)
        new_filename = f"{base}_blured{ext}"
        new_filepath = os.path.join(folder, new_filename)
        blurred.save(new_filepath)
        return new_filepath

    return await asyncio.to_thread(_blur_sync, filepath)

# -------------------
# HANDLERS
# -------------------
def register_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(payments_router)
    register_crypto_handlers(dp)
    load_agreed_users()

    # ===== START =====
    @dp.message(Command("start"))
    async def start_handler(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if is_user_agreed(user_id):
            await state.set_state(UserStates.MAIN_MENU)
            await message.answer("Welcome back! Choose an option:", reply_markup=main_menu)
        else:
            await send_user_agreement(message)

    async def send_user_agreement(message: types.Message):
        await message.answer(
            "📜 *User Agreement*\n\n"
            "By using this bot, you agree to the following terms:\n"
            "1. You will not use this bot for any illegal activities.\n"
            "2. You will not attempt to hack or disrupt the bot's services.\n\n"
            "🎁 As a gift, you will receive 20 free credits upon agreeing to these terms.",
            reply_markup=get_user_agreement_keyboard(),
            parse_mode="Markdown"
        )

    @dp.callback_query(lambda c: c.data == "agree")
    async def on_agree(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if not is_user_agreed(user_id):
            user_agreed.add(user_id)
            save_agreed_users(user_agreed)
            add_credits(user_id, 20)
            await log_message("User agreed to the terms and received 20 credits", user_id)
            await callback.message.answer("🎉 Thank you for agreeing! You have been credited with 20 free credits.")
        await state.set_state(UserStates.MAIN_MENU)
        await callback.message.edit_text("You agreed! ✅")
        await callback.message.answer(
            'Click "📸 Send photo" to upload an image and I\'ll process it for you.',
            reply_markup=main_menu
        )
        await callback.answer()

    # ===== PAYMENT METHOD =====
    @dp.callback_query(lambda c: c.data in ["pay_stars", "pay_crypto"])
    async def choose_payment_method(callback: types.CallbackQuery, state: FSMContext):
        if callback.data == "pay_stars":
            await state.set_state(UserStates.BUY_CREDITS)
            await callback.message.answer("Select a package to buy:", reply_markup=buy_credits_keyboard())
        elif callback.data == "pay_crypto":
            await state.set_state(UserStates.BUY_CREDITS)
            await callback.message.answer("Выберите действие через CryptoBot:", reply_markup=crypto_credits_menu)
        await callback.answer()

    # ===== GLOBAL HANDLER =====
    @dp.message()
    async def global_handler(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if message.from_user.is_bot:
            return

        if not is_user_agreed(user_id):
            await send_user_agreement(message)
            return

        current_state = await state.get_state()
        if current_state is None:
            current_state = UserStates.MAIN_MENU.state

        # ---------- Back to main menu ----------
        if message.text == "⬅️ Back to menu":
            await state.set_state(UserStates.MAIN_MENU)
            await message.answer("🏠 Back to main menu. Choose an option:", reply_markup=main_menu)
            return

        # ---------- Main menu buttons ----------
        if message.text == "📸 Send photo":
            await state.set_state(UserStates.SEND_PHOTO)
            await message.answer("Please upload a photo and I'll process it.", reply_markup=send_photo_menu)
            return

        if message.text == "💳 Buy credits":
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="⭐ Stars", callback_data="pay_stars")],
                    [InlineKeyboardButton(text="💰 Crypto", callback_data="pay_crypto")]
                ]
            )
            await message.answer("Choose payment method:", reply_markup=keyboard)
            return

        if message.text == "💰 Show my credits":
            user_credits = get_user_credits(user_id)
            await message.answer(f"💰 You have {user_credits} credits.", reply_markup=main_menu)
            return

        if message.text == "🌐 Language":
            await message.answer("Скоро будет добавлено", reply_markup=main_menu)
            return

        if message.text == "🛠 Support":
            await message.answer("Связаться с нами можно через gmail@help.com", reply_markup=main_menu)
            return

        # ---------- Photo processing ----------
        if message.photo and current_state == UserStates.SEND_PHOTO.state:
            user_credits = get_user_credits(user_id)
            if user_credits < 10:
                await message.answer("⚠️ You don't have enough credits (10 required).")
                return

            if not spend_credits(user_id, 10):
                await message.answer("⚠️ Could not spend credits. Try again later.")
                return

            await message.answer("✅ Got your photo. Processing... 10 credits spent.")
            file_path = await save_photo(message, bot)
            file_full_path = os.path.abspath(file_path)
            file_name = os.path.basename(file_path)

            time_start = time.time()
            processed_image = await call_runpod_api(IMAGE_PATH=file_full_path, image_name=file_name, user_id=user_id)
            time_end = time.time()

            if processed_image is None:
                await message.answer("❌ Error processing the image.")
                add_credits(user_id, 10)
                return

            await log_message(f"Processed image in {time_end - time_start:.2f}s", user_id)
            blured_image = await blur_image(processed_image)
            await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile(blured_image), caption="Here is your blurred image!")
            os.remove(blured_image)
            await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile(processed_image), caption="Here is your image!")
