from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from payments_stars import CREDIT_PACKAGES

# -------------------
# MAIN MENU KEYBOARDS
# -------------------

photo_selection_list = ["📸 Send photo", "📸 Отправить фото"]
buy_credits_section_list = ["💳 Buy credits", "💳 Купить кредиты"]
language_selection_list = ["🌐 Language", "🌐 Язык"]
credits_selection_list = ["💰 Show my credits", "💰 Показать мои кредиты"]
back_to_menu_list = ["⬅️ Back to menu", "⬅️ Назад в меню"]
pay_stars_list = ["⭐ Pay stars", "⭐ Оплатить звезды"]
pay_crypto_list = ["💰 Pay crypto (🔥 -10%)", "💰 Оплатить криптовалютой (🔥 -10%)"]
pay_usd_list = ["Pay USDT 🟢", "Оплата по USDT 🟢", "Pay USDC 🔵", "Оплата по USDC 🔵"]
back_to_payment_methods_list = ["⬅️ Back to payment methods", "⬅️ Назад к способам оплаты"]


def main_menu(language):
    from handlers import get_text

    send_photo = get_text("photo_selection", language=language)
    buy_credits = get_text("buy_credits_selection", language=language)
    language_btn = get_text("language_selection", language=language)
    show_credits = get_text("credits_selection", language=language)

    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=send_photo), KeyboardButton(text=buy_credits)],
            [KeyboardButton(text=language_btn), KeyboardButton(text=show_credits)]
        ],
        resize_keyboard=True
    )

    return main_menu

def send_photo_menu(language):
    from handlers import get_text

    back_to_menu = get_text("back_to_menu_selection", language=language)

    send_photo_menu = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=back_to_menu)]],
        resize_keyboard=True
    )
    return send_photo_menu


def buy_credits_reply_menu(language):
    from handlers import get_text

    pay_stars = get_text("pay_stars_section", language=language)
    pay_crypto = get_text("pay_crypto_section", language=language)
    back_to_menu = get_text("back_to_menu_selection", language=language)

    buy_credits_reply_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=pay_stars), KeyboardButton(text=pay_crypto)],
            [KeyboardButton(text=back_to_menu)]
        ],
        resize_keyboard=True
    )
    return buy_credits_reply_menu