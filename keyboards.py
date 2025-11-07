from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from payments_stars import CREDIT_PACKAGES

# -------------------
# MAIN MENU KEYBOARDS
# -------------------

languages = ["en", "ru", "de", "es", "fr", "it", "pt", "pl"]


languages_dict = {
    "🇬🇧 EN": "en",
    "🇷🇺 RU": "ru",
    "🇩🇪 DE": "de",
    "🇪🇸 ES": "es",
    "🇫🇷 FR": "fr",
    "🇮🇹 IT": "it",
    "🇵🇹 PT": "pt",
    "🇵🇱 PL": "pl"
}

def get_section(section):
    from handlers import get_text

    texts = [get_text(section, language=lang) for lang in languages]
    return texts

def get_usd():
    from handlers import get_text

    usdt = [get_text("pay_usdt", language=lang) for lang in languages]
    usdc = [get_text("pay_usdc", language=lang) for lang in languages]

    return usdt + usdc


photo_selection_list = get_section("photo_selection")
buy_credits_section_list = get_section("buy_credits_selection")
language_selection_list = get_section("language_selection")
credits_selection_list = get_section("credits_selection")
back_to_menu_list = get_section("back_to_menu_selection")
pay_stars_list = get_section("pay_stars_section")
pay_crypto_list = get_section("pay_crypto_section")
pay_usd_list = get_usd()    
back_to_payment_methods_list = get_section("back_to_payment_methods")


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



def language_change():

    buttons = [KeyboardButton(text=key) for key in languages_dict.keys()]
    
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


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

    # pay_stars = get_text("pay_stars_section", language=language)
    pay_crypto = get_text("pay_crypto_section", language=language)
    back_to_menu = get_text("back_to_menu_selection", language=language)

    buy_credits_reply_menu = ReplyKeyboardMarkup(
        keyboard=[
            [ KeyboardButton(text=pay_crypto)], # KeyboardButton(text=pay_stars)
            [KeyboardButton(text=back_to_menu)]
        ],
        resize_keyboard=True
    )
    return buy_credits_reply_menu