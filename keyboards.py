from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from payments_stars import CREDIT_PACKAGES

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📸 Send photo"), KeyboardButton(text="💳 Buy credits")],
        [KeyboardButton(text="🌐 Language"), KeyboardButton(text="🛠 Support")]
    ],
    resize_keyboard=True
)

# Меню отправки фото
send_photo_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Back to menu")]],
    resize_keyboard=True
)

# Меню покупки кредитов


buy_credits_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Buy credits"), KeyboardButton(text="💰 Show my credits")],
        [KeyboardButton(text="⬅️ Back to menu")]
    ],
    resize_keyboard=True
)

# Кнопки пакетов кредитов
def buy_credits_keyboard():
    keyboard = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)

    for pkg_id, pkg in CREDIT_PACKAGES.items():
        keyboard.add(KeyboardButton(text=pkg["name"]))
    keyboard.add(KeyboardButton(text="⬅️ Back to menu"))
    return keyboard

# Кнопки соглашения пользователя
def get_user_agreement_keyboard():
    keyboard = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)

    keyboard.add(KeyboardButton(text="Agree ✅", callback_data="agree"))
    return keyboard
