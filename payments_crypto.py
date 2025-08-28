# payments_crypto.py
import os
import requests
from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from handlers import add_credits, get_user_credits
from logs import log_message

router = Router()

API_TOKEN = os.getenv("TELEGRAM_PAYMENT_TOKEN_CRYPTO_BOT")
if not API_TOKEN:
    raise ValueError("❌ TELEGRAM_PAYMENT_TOKEN_CRYPTO_BOT не найден в .env")

CREDIT_PACKAGES_CRYPTO = {
    "crypto_100": {"credits": 100, "price": "0.1"},   # 1 USDT
    "crypto_550": {"credits": 550, "price": "5"},   # 5 USDT
    "crypto_1200": {"credits": 1200, "price": "10"} # 10 USDT
}

def buy_credits_crypto_keyboard():
    keyboard = []
    for key, pkg in CREDIT_PACKAGES_CRYPTO.items():
        btn = InlineKeyboardButton(
            text=f"{pkg['credits']} credits - {pkg['price']} USDT",
            callback_data=key
        )
        keyboard.append([btn])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Создание инвойса
def create_invoice(amount):
    headers = {'Crypto-Pay-API-Token': API_TOKEN}
    data = {"asset": "USDT", "amount": amount}
    resp = requests.post("https://pay.crypt.bot/api/createInvoice", headers=headers, json=data)
    if resp.ok:
        res = resp.json()["result"]
        return res["pay_url"], res["invoice_id"]
    return None, None

# Проверка инвойса
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
    user_id = callback.from_user.id
    package = CREDIT_PACKAGES_CRYPTO.get(callback.data)
    if not package:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return

    pay_url, invoice_id = create_invoice(package["price"])
    if not pay_url:
        await callback.message.answer("❌ Ошибка при создании счета")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Оплатить {package['price']} USDT", url=pay_url)],
        [InlineKeyboardButton(text="Проверить оплату", callback_data=f"check_crypto_{invoice_id}_{package['credits']}")]
    ])
    await callback.message.answer(
        f"Для оплаты {package['credits']} credits перейдите по ссылке:",
        reply_markup=kb
    )

@router.callback_query(lambda c: c.data.startswith("check_crypto_"))
async def check_crypto_payment(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    invoice_id, credits_amount = parts[2], int(parts[3])

    status = check_invoice(invoice_id)
    if status and status.get("ok"):
        inv = next((i for i in status["result"]["items"] if str(i["invoice_id"]) == invoice_id), None)
        if inv and inv["status"] == "paid":
            add_credits(callback.from_user.id, credits_amount)
            user_credits = get_user_credits(callback.from_user.id)
            await log_message(f"Crypto payment success: +{credits_amount} credits", callback.from_user.id)
            await callback.message.answer(f"✅ Оплата прошла! Вам начислено {credits_amount} credits.\n💰 Теперь у вас {user_credits} credits.")
            await callback.answer()
            return
    await callback.answer("❌ Оплата не найдена", show_alert=True)

def register_crypto_handlers(dp):
    dp.include_router(router)
    for key in CREDIT_PACKAGES_CRYPTO.keys():
        @router.callback_query(lambda c, k=key: c.data == k)
        async def _(callback: types.CallbackQuery, k=key):
            await handle_buy_crypto(callback)
