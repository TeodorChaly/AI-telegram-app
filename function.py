import asyncio
import json
import random
import string
import os
from PIL import Image, ImageFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from stats.checker import *
from aiogram import types
from dotenv import load_dotenv
from database import get_user

load_dotenv()

# -------------------
# Credits system
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
# Photo handling
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

async def save_document_as_image(message, bot) -> str:
    file_info = await bot.get_file(message.document.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)

    random_letters = ''.join(random.choices(string.ascii_lowercase, k=10))
    filename = f"{message.from_user.id}_{random_letters}.jpg"

    folder = "photos"
    await asyncio.to_thread(os.makedirs, folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    def write_and_compress():
        with open(filepath, "wb") as f:
            f.write(downloaded_file.read())

        img = Image.open(filepath).convert("RGB")
        max_size = 1024
        img.thumbnail((max_size, max_size))
        img.save(filepath, "JPEG", quality=85)

    await asyncio.to_thread(write_and_compress)
    return filepath

async def save_webp_as_jpg(file_id: str, bot, user_id: int) -> str:
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    os.makedirs("photos", exist_ok=True)
    random_letters = ''.join(random.choices(string.ascii_lowercase, k=10))
    jpg_name = f"photos/{user_id}_{random_letters}.jpg"

    downloaded_file = await bot.download_file(file_path)

    def convert():
        with open("temp.webp", "wb") as f:
            f.write(downloaded_file.read())

        img = Image.open("temp.webp").convert("RGB")
        max_size = 1024
        img.thumbnail((max_size, max_size))
        img.save(jpg_name, "JPEG", quality=85)
        os.remove("temp.webp")

    await asyncio.to_thread(convert)
    return jpg_name



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

    new_filepath = await asyncio.to_thread(_blur_sync, filepath)
    return new_filepath

def choose_text_by_language(part_of_text, language_code):
    from keyboards import languages

    if language_code not in languages:
        language_code = "en"

    lang_folder = f"lang"
    os.makedirs(lang_folder, exist_ok=True)

    with open(f"{lang_folder}/lang_{language_code}.json", "r", encoding="utf-8") as f:
        texts = json.load(f)

    if part_of_text in texts:
        return texts[part_of_text]


def get_text(part, user_id=None, language=None):
    if language:
        language = language

    text = choose_text_by_language(part, language)

    return text


# -------------------
# User agreements
# -------------------
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

def is_user_agreed(user_id: int) -> bool:
    return user_id in user_agreed

def get_user_agreement_keyboard(message):
    from handlers import get_text, get_user_language

    language = get_user_language(message.from_user.id)
    agreement = get_text("button", language=language)


    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=agreement, callback_data="agree")]
    ])

SUBSCRIBED_USERS_FILE = "subscribed_users.json"

async def check_status(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ID_CHANEL = os.getenv("TELEGRAM_ID_CHANEL")
    
    try:
        member = await callback.bot.get_chat_member(chat_id=ID_CHANEL, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
        else:
            return False
    except Exception:
        return False
    



async def is_user_subscribed(user_id: int) -> bool:
    if not os.path.exists(SUBSCRIBED_USERS_FILE):
        return False

    with open(SUBSCRIBED_USERS_FILE, "r") as f:
        try:
            subscribed_users = json.load(f)
        except json.JSONDecodeError:
            return False

    for user in subscribed_users:
        if user.get("user_id") == user_id:
            return True

    return False


async def save_subscribed_user(callback: types.CallbackQuery, user_id: int) -> bool:
    if not os.path.exists(SUBSCRIBED_USERS_FILE):
        with open(SUBSCRIBED_USERS_FILE, "w") as f:
            json.dump([], f)

    if await is_user_subscribed(user_id):
        return False 

    with open(SUBSCRIBED_USERS_FILE, "r") as f:
        try:
            subscribed_users = json.load(f)
        except json.JSONDecodeError:
            subscribed_users = []

    new_user = {
        "user_id": user_id,
        "date": datetime.utcnow().isoformat()
    }
    subscribed_users.append(new_user)

    with open(SUBSCRIBED_USERS_FILE, "w") as f:
        json.dump(subscribed_users, f, indent=4)

    return True


async def is_user_subscribed_db(user_id: int) -> bool:

    user_info = get_user(user_id)

    if user_info:
        if user_info[3] == 1:
            return True
        else:
            return False
    else:
        return True
    

async def save_subscribed_user_db(user_id: int) -> bool:
    if await is_user_subscribed_db(user_id):
        return False 

    from database import update_user
    update_user(user_id=user_id, subscribed_status=True)

    return True
