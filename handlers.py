# handlers.py
import math
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
from stats.checker import *
from aiogram.types import InputMediaVideo

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
            add_credits(user_id, 5)
            user = callback.from_user
            await add_value("new_users_today")
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
                await callback.message.answer("Thanks you for your subsciption. You got 5 free credits!")
                try:
                    add_credits(user_id, 5)
                    await add_value("subscribed")
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
            await add_value("language")
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
            await add_value("look_to_buy")
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
            await add_value("look_to_buy_stars")
            await state.set_state(UserStates.BUY_CREDITS)
            await message.answer("Select a package to buy:", reply_markup=buy_credits_keyboard())
            return

        if message.text == "💰 Pay crypto (🔥 -10%)":
            await add_value("look_to_buy_crypto")
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

            file_path = await save_webp_as_jpg(message.sticker.file_id, bot, message.from_user.id)

        
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Photo (10 credits)", callback_data=f"process_photo:{file_path}")],
                [InlineKeyboardButton(text="Video (20 credits) - New 🔥", callback_data=f"process_video:{file_path}")]
            ])
            await message.answer(
                "Choose how you want to process the file:",
                reply_markup=keyboard
            )

        elif message.sticker and current_state != UserStates.SEND_PHOTO.state:
            await message.answer("Please, go to '📸 Send photo' section")


        # --------- Photo processing ----------
        if (message.photo or message.document) and current_state == UserStates.SEND_PHOTO.state:
            user_credits = get_user_credits(user_id)

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


            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Photo (10 credits)", callback_data=f"process_photo:{file_path}")],
                [InlineKeyboardButton(text="Video (20 credits) - New 🔥", callback_data=f"process_video:{file_path}")]
            ])
            await message.reply(
"""✅ Got your image. Choose how you want to process the photo:""",
                reply_markup=keyboard
            )

        elif (message.photo or message.document) and current_state != UserStates.SEND_PHOTO.state:
            await message.answer("Please, go to '📸 Send photo' section")

    @dp.callback_query(lambda c: c.data.startswith("process_"))
    async def process_file_callback(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        data = callback.data
        action, file_path = data.split(":", 1) 

        try:
            await callback.message.delete()
        except Exception:
            pass  

        file_name = os.path.basename(file_path)
        time_start = time.time()

        if action == "process_photo":

            user_credits = get_user_credits(user_id)
            if user_credits < 10:
                await callback.message.answer("⚠️ You don't have enough credits (10 required). \nYou can buy credits in '💳 Buy credits' section.")
                await callback.answer()
                return

            if not spend_credits(user_id, 10):
                await callback.message.answer("⚠️ Could not spend credits. Try again later.")
                await callback.answer()
                return
            
            

            status_message = await callback.message.answer(
    "✅ The process will take 30–40 seconds... 10 credits spent."
)
            processed_image = await call_runpod_api(IMAGE_PATH=file_path, image_name=file_name, user_id=user_id)

            if processed_image:
                try:
                    await status_message.delete()
                except Exception:
                    pass

                time_end = time.time()
                await add_value("processing_time", int(time_end - time_start))
                await add_value("sended_photo")

                await bot.send_photo(chat_id=callback.message.chat.id, photo=FSInputFile(processed_image))

                try:
                    os.remove(processed_image)  
                    os.remove(file_path)       
                except Exception as e:
                    print(f"Error while deleting: {e}")

            else:
                try:
                    await callback.message.delete()
                except Exception:
                    pass  
                await callback.message.answer("❌ Error processing the image.")
                add_credits(user_id, 10)

        elif action == "process_video":

            effects_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Effect 1 🔥", callback_data=f"video_effect:effect1:{file_path}")],
                [InlineKeyboardButton(text="Effect 2 ✨", callback_data=f"video_effect:effect2:{file_path}")]
            ])
            await callback.message.answer("Choose a video effect:", reply_markup=effects_keyboard)



    @dp.callback_query(lambda c: c.data.startswith("video_effect:"))
    async def process_video_effect(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        _, effect_name, file_path = callback.data.split(":", 2)

        try:
            await callback.message.delete()
        except Exception:
            pass

        user_credits = get_user_credits(user_id)
        if user_credits < 20:
                await callback.message.answer("⚠️ You don't have enough credits (20 required). \nYou can buy credits in '💳 Buy credits' section.")
                await callback.answer()
                return

        if not spend_credits(user_id, 20):
                await callback.message.answer("⚠️ Could not spend credits. Try again later.")
                await callback.answer()
                return
        
        time_start = time.time()

        status_message = await callback.message.answer("✅ The process will take 3-4 minutes... 20 credits spent.")
        processed_video = await call_runpod_api_video(
            IMAGE_PATH=file_path,
            image_name=os.path.basename(file_path),
            user_id=user_id,
            effect=effect_name 
        )

        if processed_video:
                try:
                    await status_message.delete()
                except Exception:
                    pass

                time_end = time.time()
                await add_value("processing_time", int(time_end - time_start))
                await add_value("sended_video")

                await bot.send_video(chat_id=callback.message.chat.id, video=FSInputFile(processed_video))

                try:
                    os.remove(processed_video)  
                    os.remove(file_path)       
                except Exception as e:
                    print(f"Error while deleting: {e}")
        else:
                await callback.message.answer("❌ Error processing the video.")
                add_credits(user_id, 20)
