import os
from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from function import add_credits, get_text, get_user_credits  # only functions
from config import PRODUCT_PRICE_STARS
from stats.checker import *



router = Router()

TELEGRAM_STARS_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not TELEGRAM_STARS_TOKEN:
    raise ValueError("TELEGRAM_STARS_TOKEN is not set")


CREDIT_PACKAGES = PRODUCT_PRICE_STARS

def buy_credits_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for buying credits"""
    keyboard = [
        [InlineKeyboardButton(text=f"{p['name']}", callback_data=k)] # - {p['price']}
        for k, p in CREDIT_PACKAGES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(lambda c: c.data in CREDIT_PACKAGES)
async def buy_credits_callback(callback: types.CallbackQuery):
    from handlers import get_user_language
    """Handle credit package selection"""
    package_id = callback.data
    package = CREDIT_PACKAGES[package_id]


    # delete the old message with package selection
    try:
        await callback.message.delete()
    except Exception as e:
        pass
    
    language = get_user_language(callback.from_user.id)
    text = get_text("purchase_credits", language=language)

    package_num = package['name']
    package_price = package['price']

    full_text = text.format(
        package_num=package_num,
        package_price=package_price
    )


    # send invoice as a new message
    await callback.message.answer_invoice(
        title=package["name"],
        description=full_text,
        payload=package_id,
        provider_token=TELEGRAM_STARS_TOKEN,
        currency="XTR",
        prices=[LabeledPrice(label=package["name"], amount=package["price"])],
        start_parameter="start_parameter"
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(query: types.PreCheckoutQuery):
    """Handle PreCheckoutQuery and add credits"""
    from handlers import get_user_language


    if query.invoice_payload in CREDIT_PACKAGES:
        await query.answer(ok=True)

        # add credits to the user
        package = CREDIT_PACKAGES[query.invoice_payload]
        try:
            add_credits(query.from_user.id, package["credits"])
            new_balance = get_user_credits(query.from_user.id)
            
            await add_value("bought_stars")
            await add_value("amount_stars", package["price"])
            
            BOT_NAME = os.getenv("BOT_NAME")

            purchase_notification = f"""
STARS - {package["price"] * 0.013} usd ({package["price"]} stars) - {BOT_NAME}
"""
            await send_message(purchase_notification)
            

            selected_package = package['credits']
            new_balance = new_balance


            language = get_user_language(query.from_user.id)
            text = get_text("balance_notification", language=language)


            balance_notification = text


            balance_notification_formatted = balance_notification.format(
                selected_package=selected_package,
                new_balance=new_balance
            )

            # notify the user about new balance
            await query.bot.send_message(
                query.from_user.id,
                balance_notification_formatted
            )

        except Exception as e:
            pass
    else:
        await query.answer(ok=False, error_message="Package not found!")