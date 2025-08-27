import os
from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from function import add_credits, get_user_credits  # только функции

router = Router()

TELEGRAM_STARS_TOKEN = os.getenv("API_TOKEN")
if not TELEGRAM_STARS_TOKEN:
    raise ValueError("TELEGRAM_STARS_TOKEN не установлен")

# Пакеты кредитов
CREDIT_PACKAGES = {
    "pack_10": {"name": "10 credits", "price": 1, "credits": 10},
    "pack_50": {"name": "50 credits", "price": 4, "credits": 50},
    "pack_100": {"name": "100 credits", "price": 9, "credits": 100},
}

def buy_credits_keyboard() -> InlineKeyboardMarkup:
    """Создание клавиатуры для покупки кредитов"""
    keyboard = [
        [InlineKeyboardButton(text=f"{p['name']} - {p['price']} ⭐", callback_data=k)]
        for k, p in CREDIT_PACKAGES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(lambda c: c.data in CREDIT_PACKAGES)
async def buy_credits_callback(callback: types.CallbackQuery):
    """Обработка выбора пакета кредитов"""
    package_id = callback.data
    package = CREDIT_PACKAGES[package_id]

    print(f"[LOG] {callback.from_user.id} выбрал пакет {package_id}")

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
    """Обработка PreCheckoutQuery и начисление кредитов"""
    print(f"[LOG] PreCheckoutQuery от {query.from_user.id}: payload={query.invoice_payload}")

    if query.invoice_payload in CREDIT_PACKAGES:
        await query.answer(ok=True)
        print(f"[LOG] PreCheckoutQuery OK для {query.from_user.id}")

        # начисляем кредиты пользователю
        package = CREDIT_PACKAGES[query.invoice_payload]
        try:
            add_credits(query.from_user.id, package["credits"])
            new_balance = get_user_credits(query.from_user.id)

            # уведомление пользователя о новом балансе
            await query.bot.send_message(
                query.from_user.id,
                f"✅ Ваши кредиты увеличились на {package['credits']}! "
                f"Теперь у вас {new_balance} кредитов."
            )
            print(f"[LOG] {query.from_user.id} получил {package['credits']} credits. New balance: {new_balance}")

        except Exception as e:
            print(f"[ERROR] Не удалось добавить кредиты для {query.from_user.id}: {e}")
    else:
        await query.answer(ok=False, error_message="Package not found!")
        print(f"[LOG] PreCheckoutQuery FAILED для {query.from_user.id}: payload={query.invoice_payload}")
