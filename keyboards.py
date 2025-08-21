from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📸 Send photo"), KeyboardButton(text="💳 Buy credits")],
        [KeyboardButton(text="🌐 Language"), KeyboardButton(text="👤 Profile")]
    ],
    resize_keyboard=True
)

send_photo_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⬅️ Back to menu")]
    ],
    resize_keyboard=True
)

buy_credits_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Buy credits"), KeyboardButton(text="💰 Show my credits")],
        [KeyboardButton(text="⬅️ Back to menu")]
    ],
    resize_keyboard=True
)