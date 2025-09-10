from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from payments_stars import CREDIT_PACKAGES

# -------------------
# MAIN MENU KEYBOARDS
# -------------------
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📸 Send photo"), KeyboardButton(text="💳 Buy credits")],
        [KeyboardButton(text="🌐 Language"), KeyboardButton(text="💰 Show my credits")]
    ],
    resize_keyboard=True
)

send_photo_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Back to menu")]],
    resize_keyboard=True
)

buy_credits_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Buy credits"), KeyboardButton(text="💰 Show my credits")],
        [KeyboardButton(text="⬅️ Back to menu")]
    ],
    resize_keyboard=True
)

buy_credits_reply_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⭐ Pay stars"), KeyboardButton(text="💰 Pay crypto (🔥 -10%)")],
        [ KeyboardButton(text="⬅️ Back to menu")]
    ],
    resize_keyboard=True
)