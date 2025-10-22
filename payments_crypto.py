import os
import requests
from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from handlers import add_credits, get_user_credits
from logs import log_message
from config import PRODUCT_PRICE_CRYPTO
from stats.checker import *

router = Router()


API_TOKEN = os.getenv("TELEGRAM_PAYMENT_TOKEN_CRYPTO_BOT")
if not API_TOKEN:
    raise ValueError("❌ TELEGRAM_PAYMENT_TOKEN_CRYPTO_BOT is missing in .env")

CREDIT_PACKAGES_CRYPTO= PRODUCT_PRICE_CRYPTO

def buy_credits_crypto_keyboard(currency="USDC"):
    keyboard = []
    for key, pkg in CREDIT_PACKAGES_CRYPTO.items():
        btn = InlineKeyboardButton(
            text=f"{pkg['credits']} credits - {pkg['price']} {currency}",
            callback_data=f"{key}_{currency}"
        )
        keyboard.append([btn])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_invoice(amount, currency="USDC"):
    headers = {'Crypto-Pay-API-Token': API_TOKEN}
    data = {"asset": currency, "amount": amount}
    resp = requests.post("https://pay.crypt.bot/api/createInvoice", headers=headers, json=data)
    if resp.ok:
        res = resp.json()["result"]
        return res["pay_url"], res["invoice_id"]
    return None, None

def check_invoice(invoice_id):
    headers = {'Crypto-Pay-API-Token': API_TOKEN}
    resp = requests.get(
        f"https://pay.crypt.bot/api/getInvoices?invoice_ids={invoice_id}",
        headers=headers
    )
    if resp.ok:
        return resp.json()
    return None

async def handle_buy_crypto(callback: types.CallbackQuery):
    from handlers import get_user_language
    from handlers import get_text

    parts = callback.data.split("_")
    package_key = "_".join(parts[:2])  
    currency = parts[2]               

    package = CREDIT_PACKAGES_CRYPTO.get(package_key)
    if not package:
        await callback.answer("❌ Package not found", show_alert=True)
        return

    pay_url, invoice_id = create_invoice(package["price"], currency=currency)
    if not pay_url:
        await callback.message.answer("❌ Error while creating invoice")
        return
    


    language = get_user_language(callback.from_user.id)

    package_num = package['price']
    pay = get_text("pay", language=language)


    pay_formatted = pay.format(
        package_num=package_num,
        currency=currency
    )

    check_payment = get_text("check_payment", language=language)

    package_credits = package['credits']
    message_to_pay = get_text("message_to_pay", language=language)
    message_to_pay_formatted = message_to_pay.format(
        package_credits=package_credits,
        currency=currency
    )



    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=pay_formatted, url=pay_url)],
        [InlineKeyboardButton(text=check_payment, callback_data=f"check_crypto_{invoice_id}_{package['credits']}")]
    ])

    await callback.message.delete()
    await callback.message.answer(
        message_to_pay_formatted,
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("check_crypto_"))
async def check_crypto_payment(callback: types.CallbackQuery):
    from handlers import get_user_language
    from handlers import get_text

    parts = callback.data.split("_")
    invoice_id, credits_amount = parts[2], int(parts[3])

    status = check_invoice(invoice_id)
    language = get_user_language(callback.from_user.id)

    if status and status.get("ok"):
        inv = next((i for i in status["result"]["items"] if str(i["invoice_id"]) == invoice_id), None)
        if inv and inv["status"] == "paid":
            add_credits(callback.from_user.id, credits_amount)
            user_credits = get_user_credits(callback.from_user.id)
            await log_message(f"Crypto payment success: +{credits_amount} credits", callback.from_user.id)
            payment = status['result']['items'][0]
            paid_amount = float(payment['paid_amount'])

            await add_value("bought_crypto")
            await add_value("amount_crypto", paid_amount)

            BOT_NAME = os.getenv("BOT_NAME")

            purchase_notification = f"""
CRYPTO - {paid_amount} usdc - {BOT_NAME}
"""
            await send_message(purchase_notification)

            
            succ = get_text("succ", language=language)

            success_formatted = succ.format(
                credits_amount=credits_amount,
                user_credits=user_credits
            )

            await callback.message.delete()
            await callback.message.answer(
                success_formatted
            )
            await callback.answer()
            return
        
    payment_not_found = get_text("payment_not_found", language=language)

    await callback.answer(payment_not_found, show_alert=True)

def register_crypto_handlers(dp):
    dp.include_router(router)
    for key in CREDIT_PACKAGES_CRYPTO.keys():
        @router.callback_query(lambda c, k=key: c.data.startswith(k + "_"))
        async def _(callback: types.CallbackQuery, k=key):
            await handle_buy_crypto(callback)