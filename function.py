import asyncio
import asyncio
import json
import random
import string
import os
from PIL import Image, ImageFilter
import os

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
)

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

    await message.reply(f"Photo saved successfully as {filename}!")

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
    # print(filepath)
    new_filepath = await asyncio.to_thread(_blur_sync, filepath)
    return new_filepath



AGREED_USERS_FILE = "agreed_users.json"

def load_agreed_users():
    try:
        with open(AGREED_USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_agreed_users(users_set):
    with open(AGREED_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(users_set), f, ensure_ascii=False, indent=2)

user_agreed = load_agreed_users()


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


def is_user_agreed(user_id: int) -> bool:
    return user_id in user_agreed

def get_user_agreement_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ I agree", callback_data="agree")]
    ])