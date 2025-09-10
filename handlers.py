# handlers.py
import os
import time
import asyncio
import random
import string
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from PIL import Image, ImageFilter

from function import *
from fsm_states import UserStates
from runpod.call_runpod import call_runpod_api
from runpod.call_runpod_video import call_runpod_api_video
from payments_stars import router as payments_router, buy_credits_keyboard
from logs import log_message
from payments_crypto import register_crypto_handlers, buy_credits_crypto_keyboard
from keyboards import *
from dotenv import load_dotenv
load_dotenv()

TEST_MODE = os.getenv("TEST_MODE", "True") == "True"

channel_url = os.getenv("TELEGRAM_CHANEL_URL")

# -------------------
# HANDLERS
# -------------------


def register_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(payments_router)
    register_crypto_handlers(dp)
    load_agreed_users()
    

    # ===== START =====
    @dp.message(Command("start"))
    async def start_handler(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if is_user_agreed(user_id):
            await state.set_state(UserStates.MAIN_MENU)
            await message.answer("Welcome back! Choose an option:", reply_markup=main_menu)
        else:
            await send_user_agreement(message)

    async def send_user_agreement(message: types.Message):
        await message.answer(
            "📜 *User Agreement*\n\n"
            "By clicking on Accept, you automatically agree to all of the above terms and conditions:\n\n"
            "1. You must be at least 18 years old to use this bot.\n"
            "2. You cannot use other people’s photos without their permission.\n"
            "3. The creation and distribution of content with minors is strictly prohibited.\n" 
            "4. You must not generate or distribute illegal, obscene, or offensive content.\n" 
            "5. All content that you generate must comply with local and international laws.\n",
            reply_markup=get_user_agreement_keyboard(),
            parse_mode="Markdown"
        )

    @dp.callback_query(lambda c: c.data == "agree")
    async def on_agree(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if not is_user_agreed(user_id):
            user_agreed.add(user_id)
            save_agreed_users(user_agreed)
            add_credits(user_id, 10)
            user = callback.from_user
            print(1)
            await log_message(
                f"New user: "
                f"{user.first_name} "
                f"{user.last_name}, "
                f"{user.username}, "
                f"{user.language_code}",
                user_id
            )

            await callback.message.answer(
    "🎉 Welcome! You've received <b>5</b> free credits as a gift for your first registration.",
    parse_mode="HTML"
)

        await state.set_state(UserStates.MAIN_MENU)
        await callback.message.edit_text("You agreed! ✅")

        subscribe_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Subscribe to channel", url=channel_url)],
        [InlineKeyboardButton(text="Check status", callback_data="check_my_subsciptions")]
        ])

        await callback.message.answer(
            "🎁 <b>Get 5 additional credits</b> by subscribing to our channel!",
            reply_markup=subscribe_keyboard,
            parse_mode="HTML"
        )

        await callback.answer()

    # ===== PAYMENT METHOD =====
    @dp.callback_query(lambda c: c.data in ["pay_stars", "pay_crypto"])
    async def choose_payment_method(callback: types.CallbackQuery, state: FSMContext):
        if callback.data == "pay_stars":
            await state.set_state(UserStates.BUY_CREDITS)
            await callback.message.answer("Select a package to buy:", reply_markup=buy_credits_keyboard())
        elif callback.data == "pay_crypto":
            keyboard = buy_credits_crypto_keyboard()
            await callback.message.answer(
                "Choose package and pay via CryptoBot:",
                reply_markup=keyboard
            )
        await callback.answer()


    # ===== CHECK CHANNEL STATUS =====
    @dp.callback_query(lambda c: c.data == "check_my_subsciptions")
    async def check_subscription_callback(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        ID_CHANEL = os.getenv("TELEGRAM_ID_CHANEL")

        try:
            member = await callback.bot.get_chat_member(chat_id=ID_CHANEL, user_id=user_id)
            if member.status in ["creator", "administrator", "member"]:
                await callback.message.answer("Thanks you for your subsciption. You got 10 free credits!")
                try:
                    add_credits(user_id, 5)
                    await callback.message.delete()
                except Exception:
                    pass  
            else:
                await callback.answer("You are not in the channel ❌", show_alert=True)
        except Exception:
            await callback.answer("You are not in the channel ❌", show_alert=True)

    # ===== GLOBAL HANDLER FOR TEXT BUTTONS =====
    @dp.message()
    async def global_handler(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if message.from_user.is_bot:
            return

        if not is_user_agreed(user_id):
            await send_user_agreement(message)
            return

        current_state = await state.get_state()
        if current_state is None:
            current_state = UserStates.MAIN_MENU.state

        # --------- Back to main menu ----------
        if message.text == "⬅️ Back to menu":
            await state.set_state(UserStates.MAIN_MENU)
            await message.answer("🏠 Back to main menu. Choose an option:", reply_markup=main_menu)
            return

        if message.text == "🌐 Language":
            await log_message(f"Needs new language", user_id)
            await message.answer("Coming soon...")
            return

        # --------- Main menu actions ----------
        if message.text == "📸 Send photo":
            await state.set_state(UserStates.SEND_PHOTO)
            await message.answer("Please upload a photo and I'll process it.", reply_markup=send_photo_menu)
            return

        if message.text == "💳 Buy credits":
            await state.set_state(UserStates.BUY_CREDITS)
            await log_message(f"Looking to buy something, maybe...", user_id)
            await message.answer("💳 Choose a payment method:", reply_markup=buy_credits_reply_menu)
            return
        
        if message.text == "💰 Show my credits":
            user_credits = get_user_credits(user_id)
            await log_message(f"User checked his credits {user_credits}", user_id)
            await message.answer(f"💰 You have {user_credits} credits.")
            return
        
        if message.text == "⬅️ Back to payment methods":
            await state.set_state(UserStates.BUY_CREDITS)
            await message.answer("💳 Choose a payment method:", reply_markup=buy_credits_reply_menu)
            return


        if message.text == "⭐ Pay stars":
            await log_message(f"User prefer stars", user_id)
            await state.set_state(UserStates.BUY_CREDITS)
            await message.answer("Select a package to buy:", reply_markup=buy_credits_keyboard())
            return

        if message.text == "💰 Pay crypto (🔥 -10%)":
            await log_message(f"User prefer crypto", user_id)
            crypto_menu = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Pay USDT 🟢"), KeyboardButton(text="Pay USDC 🔵")],
                    [KeyboardButton(text="⬅️ Back to payment methods")]
                ],
                resize_keyboard=True
            )
            await message.answer(
                "Choose cryptocurrency to pay with:",
                reply_markup=crypto_menu
            )
            await state.set_state(UserStates.BUY_CREDITS)
            return
        
        if message.text in ["Pay USDT 🟢", "Pay USDC 🔵"]:
            if message.text.count("USDT") >= 1:
                currency = "USDT"
                keyboard = buy_credits_crypto_keyboard(currency=currency)
                await message.answer(
                    f"Pay with {currency} via CryptoBot:",
                    reply_markup=keyboard
                )
                return
            if message.text.count("USDC") >= 1:
                currency = "USDC"
                keyboard = buy_credits_crypto_keyboard(currency=currency)
                await message.answer(
                    f"Pay with {currency} via CryptoBot:",
                    reply_markup=keyboard
                )
                return
        
        if message.sticker and current_state == UserStates.SEND_PHOTO.state:
            user_credits = get_user_credits(user_id)
            if user_credits < 10:
                await message.answer("⚠️ You don't have enough credits (10 required).")
                return

            if not spend_credits(user_id, 10):
                await message.answer("⚠️ Could not spend credits. Try again later.")
                return

            file_path = await save_webp_as_jpg(message.sticker.file_id, bot, message.from_user.id)

            await message.reply("✅ Got your image. Processing... 10 credits spent.")
            
            file_full_path = os.path.abspath(file_path)
            file_name = os.path.basename(file_path)

            time_start = time.time()
            processed_image = await call_runpod_api(
                IMAGE_PATH=file_full_path, image_name=file_name, user_id=user_id
            )
            time_end = time.time()

            if processed_image is None:
                await message.answer("❌ Error processing the image.")
                add_credits(user_id, 5)
                return

            await log_message(f"Processed image {file_name} in {time_end - time_start:.2f}s", user_id)
            await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile(processed_image), caption="Here is your image!")
        elif message.sticker and current_state != UserStates.SEND_PHOTO.state:
            await message.answer("Please, go to '📸 Send photo' section")



        # --------- Photo processing ----------
        if (message.photo or message.document) and current_state == UserStates.SEND_PHOTO.state:
            user_credits = get_user_credits(user_id)
            if user_credits < 10:
                await message.answer("⚠️ You don't have enough credits (10 required).")
                return

            if not spend_credits(user_id, 10):
                await message.answer("⚠️ Could not spend credits. Try again later.")
                return

            await message.reply("✅ Got your image. Processing... 10 credits spent.")

            if message.photo:
                file_path = await save_photo(message, bot)
            elif message.document:
                mime_type = message.document.mime_type or ""
                file_name = message.document.file_name.lower()
                image_ext = (".png", ".jpg", ".jpeg", ".webp")

                if mime_type.startswith("image/") or file_name.endswith(image_ext):
                    file_path = await save_document_as_image(message, bot)
                else:
                    await message.answer("❌ This document is not an image.")
                    return
            else:
                return

            file_full_path = os.path.abspath(file_path)
            file_name = os.path.basename(file_path)

            time_start = time.time()
            processed_image = await call_runpod_api(
                IMAGE_PATH=file_full_path, image_name=file_name, user_id=user_id
            )
            # processed_video = await call_runpod_api_video(
            #     IMAGE_PATH=file_full_path, image_name=file_name, user_id=user_id
            # )
            # await bot.send_video(
            #         chat_id=message.chat.id,
            #         video=FSInputFile(processed_video),
            #         caption="Here is your video!"
            #     )
            
            time_end = time.time()

            if processed_image is None:
                await message.answer("❌ Error processing the image.")
                add_credits(user_id, 10)
                return

            await log_message(f"Processed image {file_name} in {time_end - time_start:.2f}s", user_id)
            await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile(processed_image), caption="Here is your image!")
        elif (message.photo or message.document) and current_state != UserStates.SEND_PHOTO.state:
            await message.answer("Please, go to '📸 Send photo' section")