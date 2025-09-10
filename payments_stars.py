import os
from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from function import add_credits, get_user_credits  # only functions
from config import PRODUCT_PRICE_STARS

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
    """Handle credit package selection"""
    package_id = callback.data
    package = CREDIT_PACKAGES[package_id]

    print(f"[LOG] {callback.from_user.id} selected package {package_id}")

    # delete the old message with package selection
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"[WARN] Could not delete message: {e}")

    # send invoice as a new message
    await callback.message.answer_invoice(
        title=package["name"],
        description=f"Purchase {package['name']} for {package['price']} Stars",
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
    print(f"[LOG] PreCheckoutQuery from {query.from_user.id}: payload={query.invoice_payload}")

    if query.invoice_payload in CREDIT_PACKAGES:
        await query.answer(ok=True)
        print(f"[LOG] PreCheckoutQuery OK for {query.from_user.id}")

        # add credits to the user
        package = CREDIT_PACKAGES[query.invoice_payload]
        try:
            add_credits(query.from_user.id, package["credits"])
            new_balance = get_user_credits(query.from_user.id)

            # notify the user about new balance
            await query.bot.send_message(
                query.from_user.id,
                f"✅ Your balance has been increased by {package['credits']} credits! "
                f"Now you have {new_balance} credits."
            )
            print(f"[LOG] {query.from_user.id} received {package['credits']} credits. New balance: {new_balance}")

        except Exception as e:
            print(f"[ERROR] Could not add credits for {query.from_user.id}: {e}")
    else:
        await query.answer(ok=False, error_message="Package not found!")
        print(f"[LOG] PreCheckoutQuery FAILED for {query.from_user.id}: payload={query.invoice_payload}")