import os
from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from function import add_credits, get_text, get_user_credits
from config import PRODUCT_PRICE_STARS

router = Router()

TELEGRAM_STARS_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not TELEGRAM_STARS_TOKEN:
    raise ValueError("TELEGRAM_STARS_TOKEN is not set")

CREDIT_PACKAGES = PRODUCT_PRICE_STARS


def buy_credits_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=f"{p['name']}", callback_data=k)]
        for k, p in CREDIT_PACKAGES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(lambda c: c.data in CREDIT_PACKAGES)
async def buy_credits_callback(callback: types.CallbackQuery):
    from handlers import get_user_language

    package_id = callback.data
    package = CREDIT_PACKAGES[package_id]

    try:
        await callback.message.delete()
    except Exception:
        pass

    language = get_user_language(callback.from_user.id)
    text = get_text("purchase_credits", language=language)

    package_num = package["name"]
    package_price = package["price"]

    full_text = text.format(package_num=package_num, package_price=package_price)

    await callback.answer()
    await callback.message.answer_invoice(
        title=package["name"],
        description=full_text,
        payload=package_id,
        provider_token=TELEGRAM_STARS_TOKEN,
        currency="XTR",  # Stars currency
        prices=[LabeledPrice(label=package["name"], amount=package["price"])],
        start_parameter="start_parameter"
    )


@router.pre_checkout_query()
async def process_pre_checkout(query: types.PreCheckoutQuery):
    try:
        await query.answer(ok=True)
        print("✅ PreCheckout completed:", query.id)
    except Exception as e:
        print("❌ Error pre_checkout:", e)
        await query.answer(ok=False, error_message="Error. Try before checkout.")