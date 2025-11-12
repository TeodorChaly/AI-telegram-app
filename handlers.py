# handlers.py
from email.mime import message
from logging.handlers import SMTPHandler
import math
import os
import time
import asyncio
import random
import string
import json
from aiogram import F, Bot, Dispatcher, types
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
from google_sheets import *
from keyboards import *
from dotenv import load_dotenv
from stats.checker import *
from aiogram.types import InputMediaVideo
from database import *

load_dotenv()

TEST_MODE = os.getenv("TEST_MODE", "True") == "True"

channel_url = os.getenv("TELEGRAM_CHANEL_URL")



def get_user_language(user_id):
   user = get_user(user_id)
   if user is None:
        language = "en" 
   else:
        language = user[4]
   return language


def register_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(payments_router)
    register_crypto_handlers(dp)
    load_agreed_users()
    user_video_messages = {}

    # ===== START =====
    @dp.message(Command("start"))
    async def start_handler(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        chat_id = message.chat.id
        language = get_user_language(user_id)

        print(f"user_id: {user_id}, chat_id: {chat_id}")
        if is_user_agreed(user_id):
            welcome_text = get_text("returning", language=language)

            await state.set_state(UserStates.MAIN_MENU)
            await message.answer(welcome_text, reply_markup=main_menu(language))
        else:
            await send_user_agreement(message)

    async def send_user_agreement(message: types.Message):
        language = get_user_language(message.from_user.id)
        agreement = get_text("conditions", language=language)

        await message.answer(
            agreement,
            reply_markup=get_user_agreement_keyboard(message),
            parse_mode="Markdown"
        )

    @dp.callback_query(lambda c: c.data == "agree")
    async def on_agree(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        language = get_user_language(user_id)
        first_time = get_text("first_time", language=language)
        agreed = get_text("agreed", language=language)
        subscription_bonus_buttons1 = get_text("subscription_bonus_buttons1", language=language)
        subscription_bonus_buttons2 = get_text("subscription_bonus_buttons2", language=language)
        subscription_bonus_description = get_text("subscription_bonus_description", language=language)

        add_user(user_id=user_id, subscribed_status=False, original_language=language)

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
                first_time,
                parse_mode="HTML", reply_markup=main_menu(language)
    )

        await state.set_state(UserStates.MAIN_MENU)
        await callback.message.edit_text(agreed)


        subscribe_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=subscription_bonus_buttons1, url=channel_url)],
        [InlineKeyboardButton(text=subscription_bonus_buttons2, callback_data="check_my_subsciptions")]
        ])

        await callback.message.answer(
            subscription_bonus_description,
            reply_markup=subscribe_keyboard,
            parse_mode="HTML"
        )


        await callback.answer()


    # ===== PAYMENT METHOD =====
    @dp.callback_query(lambda c: c.data in ["pay_stars", "pay_crypto"])
    async def choose_payment_method(callback: types.CallbackQuery, state: FSMContext):
        language = get_user_language(callback.from_user.id)
        buy_credits_payment_methods_stars_select_package = get_text("buy_credits_payment_methods_stars_select_package", language=language)
        buy_credits_payment_methods_crypto_description_1 = get_text("buy_credits_payment_methods_crypto_description_1", language=language)

        if callback.data == "pay_stars":
            await state.set_state(UserStates.BUY_CREDITS)
            await callback.message.answer(buy_credits_payment_methods_stars_select_package, reply_markup=buy_credits_keyboard())
        elif callback.data == "pay_crypto":
            keyboard = buy_credits_crypto_keyboard()
            await callback.message.answer(
                buy_credits_payment_methods_crypto_description_1,
                reply_markup=keyboard
            )
        await callback.answer()



    @dp.callback_query(lambda c: c.data == "subscribe_to_channel")
    async def subscribe_to_channel_callback(callback: types.CallbackQuery):
        try:
            await callback.message.delete()
        except Exception:
            pass
        language = get_user_language(callback.from_user.id)

        subscription_bonus_buttons1 = get_text("subscription_bonus_buttons1", language=language) 
        subscription_bonus_buttons2 = get_text("subscription_bonus_buttons2", language=language) 
        subscription_bonus_description = get_text("subscription_bonus_description", language=language) 

        subscribe_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=subscription_bonus_buttons1, url=channel_url)],
            [InlineKeyboardButton(text=subscription_bonus_buttons2, callback_data="check_my_subsciptions")]
        ])

        await callback.message.answer(
            subscription_bonus_description,
            reply_markup=subscribe_keyboard,
            parse_mode="HTML"
        )

        await callback.answer()



    # ===== CHECK CHANNEL STATUS =====
    @dp.callback_query(lambda c: c.data == "check_my_subsciptions")
    async def check_subscription_callback(callback: types.CallbackQuery):
        language = get_user_language(callback.from_user.id)

        thank_for_subscription = get_text("thank_for_subscription", language=language) 
        cancel = get_text("cancel", language=language) 


        user_id = callback.from_user.id
        ID_CHANEL = os.getenv("TELEGRAM_ID_CHANEL")

        try:
            member = await callback.bot.get_chat_member(chat_id=ID_CHANEL, user_id=user_id)
            if member.status in ["creator", "administrator", "member"]:
                try:
                    
                    
                    status = await save_subscribed_user(callback, user_id)
                    status_2 = await save_subscribed_user_db(user_id)
                    print("Subscription status saved:", status, status_2)

                    if status and status_2:
                        await callback.message.answer(thank_for_subscription)
                        add_credits(user_id, 5)
                        await add_value("subscribed")

                    await callback.message.delete()
                except Exception:
                    pass  
            else:
                await callback.answer(cancel, show_alert=True)
        except Exception:
            await callback.answer(cancel, show_alert=True)

    @dp.message(F.successful_payment)
    async def handle_successful_payment(message: types.Message):
        payment = message.successful_payment
        user_id = message.from_user.id
        package_id = payment.invoice_payload

        if package_id not in CREDIT_PACKAGES:
            await message.answer("❌ Error: unsupported package")
            return

        package = CREDIT_PACKAGES[package_id]
        credits_to_add = package.get("credits", 0)
        add_credits(user_id, credits_to_add)

        BOT_NAME = os.getenv("BOT_NAME")
        purchase_notification = f"""
STARS - {package["price"] * 0.013} usd ({package["price"]} stars) - {BOT_NAME} from @{message.from_user.username}
"""
        await send_message(purchase_notification)
        await update_google_sheet(package["price"] * 0.013) 

        await add_value("bought_stars")
        await add_value("amount_stars", package["price"])

        language = get_user_language(user_id)
        text_template = get_text("balance_notification", language=language)

        new_balance = get_user_credits(message.from_user.id)
        selected_package = package['credits']
        success_text = text_template.format(selected_package=selected_package, new_balance=new_balance)
        balance = get_user_credits(user_id)

        await message.answer(f"{success_text}\n\nCurrent balance: {balance}⭐️")


    # ===== GLOBAL HANDLER FOR TEXT BUTTONS =====
    @dp.message()
    async def global_handler(message: types.Message, state: FSMContext):
        language = get_user_language(message.from_user.id)
        back_to_menu = get_text("back_to_menu", language=language)
        language_text = get_text("language", language=language)
        upload_photo = get_text("upload_photo", language=language)
        choose_payment_method = get_text("choose_payment_method", language=language)
        show_my_credits = get_text("show_my_credits", language=language)
        select_a_package = get_text("select_a_package", language=language)
        pay_usdc = get_text("pay_usdc", language=language)
        pay_usdt = get_text("pay_usdt", language=language)
        back_to_payment_methods = get_text("back_to_payment_methods", language=language)
        crypto_to_pay = get_text("crypto_to_pay", language=language)
        pay_currecny = get_text("pay_currecny", language=language)
        photo = get_text("photo", language=language)
        video = get_text("video", language=language)
        process_photo_options = get_text("process_photo_options", language=language)
        got_your_image = get_text("got_your_image", language=language)
        not_an_image = get_text("not_an_image", language=language)

        user_id = message.from_user.id
        if message.from_user.is_bot:
            return

        if not is_user_agreed(user_id):
            await send_user_agreement(message)
            return
        

        if message.text is not None:
            selected_text = message.text.strip()

            from keyboards import languages_dict

            if selected_text in languages_dict:
                selected_lang = languages_dict[selected_text]


                if user_exists(user_id):
                    update_user(user_id=user_id, original_language=selected_lang)
                else:
                    add_user(user_id=user_id, subscribed_status=True, original_language=selected_lang)
                    
                await state.set_state(UserStates.MAIN_MENU)
                await message.answer(
                    get_text("back_to_menu", language=selected_lang),
                    reply_markup=main_menu(selected_lang)
                )
                print(f"User {user_id} selected language: {selected_lang}")

        current_state = await state.get_state()
        if current_state is None:
            current_state = UserStates.MAIN_MENU.state

        # --------- Back to main menu ----------
        if message.text in back_to_menu_list:
            await state.set_state(UserStates.MAIN_MENU)
            await message.answer(back_to_menu, reply_markup=main_menu(language))
            return

        if message.text in language_selection_list:
            await add_value("language")
            await log_message(f"Needs new language", user_id)
            await message.answer("Choose a language:", reply_markup=language_change())
            return

        # --------- Main menu actions ----------
        if message.text in photo_selection_list:
            await state.set_state(UserStates.SEND_PHOTO)
            await message.answer(upload_photo, reply_markup=send_photo_menu(language))
            return

        if message.text in buy_credits_section_list:
            await state.set_state(UserStates.BUY_CREDITS)
            await log_message(f"Looking to buy something, maybe...", user_id)
            await add_value("look_to_buy")
            await message.answer(choose_payment_method, reply_markup=buy_credits_reply_menu(language))
            return

        if message.text in credits_selection_list:
            user_credits = get_user_credits(user_id)
            await log_message(f"User checked his credits {user_credits}", user_id)
            await message.answer(show_my_credits.format(credits=user_credits))
            return

        if message.text in back_to_payment_methods_list:
            await state.set_state(UserStates.BUY_CREDITS)
            await message.answer(choose_payment_method, reply_markup=buy_credits_reply_menu(language))
            return


        if message.text in pay_stars_list:
            await log_message(f"User prefer stars", user_id)
            await add_value("look_to_buy_stars")
            await state.set_state(UserStates.BUY_CREDITS)
            await message.answer(select_a_package, reply_markup=buy_credits_keyboard())
            return

        if message.text in pay_crypto_list:
            await add_value("look_to_buy_crypto")
            await log_message(f"User prefer crypto", user_id)
            crypto_menu = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=pay_usdt), KeyboardButton(text=pay_usdc)],
                    [KeyboardButton(text=back_to_payment_methods)]
                ],
                resize_keyboard=True
            )
            await message.answer(
                crypto_to_pay,
                reply_markup=crypto_menu
            )
            await state.set_state(UserStates.BUY_CREDITS)
            return

        if message.text in pay_usd_list:
            if message.text.count("USDT") >= 1:
                currency = "USDT"
                keyboard = buy_credits_crypto_keyboard(currency=currency)
                await message.answer(
                    pay_currecny.format(currency=currency),
                    reply_markup=keyboard
                )
                return
            if message.text.count("USDC") >= 1:
                currency = "USDC"
                keyboard = buy_credits_crypto_keyboard(currency=currency)
                await message.answer(
                    pay_currecny.format(currency=currency),
                    reply_markup=keyboard
                )
                return
        
        if message.sticker and current_state: # == UserStates.SEND_PHOTO.state
            user_credits = get_user_credits(user_id)

            file_path = await save_webp_as_jpg(message.sticker.file_id, bot, message.from_user.id)

        
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=photo, callback_data=f"process_photo:{file_path}")],
                [InlineKeyboardButton(text=video, callback_data=f"process_video:{file_path}")]
            ])
            await message.answer(
                process_photo_options,
                reply_markup=keyboard
            )

        # elif message.sticker and current_state != UserStates.SEND_PHOTO.state:
        #     await message.answer("Please, go to '📸 Send photo' section 2")


        # --------- Photo processing ----------
        if (message.photo or message.document): # and current_state == UserStates.SEND_PHOTO.state
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
                    await message.answer(not_an_image)
                    return
            else:
                return


            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=photo, callback_data=f"process_photo:{file_path}")],
                [InlineKeyboardButton(text=video, callback_data=f"process_video:{file_path}")]
            ])
            await message.reply(
                got_your_image,
                reply_markup=keyboard
            )

        # elif (message.photo or message.document) and current_state != UserStates.SEND_PHOTO.state: 
        #     await message.answer("Please, go to '📸 Send photo' section 1")

    

    @dp.callback_query(lambda c: c.data.startswith("process_"))
    async def process_file_callback(callback: types.CallbackQuery):
        language = get_user_language(callback.from_user.id)
        buy_credits = get_text("buy_credits", language=language)
        balance_not_enough_10 = get_text("balance_not_enough_10", language=language)
        get_5_free_credits = get_text("get_5_free_credits", language=language)
        could_not_spend_credits = get_text("could_not_spend_credits", language=language)
        process_time = get_text("process_time", language=language)
        error_processing_image = get_text("error_processing_image", language=language)
        effect_undress = get_text("effect_undress", language=language)
        effect_cloth_off_trend = get_text("effect_cloth_off_trend", language=language)
        effect_rip_her_clothes = get_text("effect_rip_her_clothes", language=language)
        effect_touch_boobs = get_text("effect_touch_boobs", language=language)
        effect_titty_drop = get_text("effect_titty_drop", language=language)
        effect_breast_play = get_text("effect_breast_play", language=language)
        video_effect = get_text("video_effect", language=language)

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
                if (await is_user_subscribed(user_id) and await is_user_subscribed_db(user_id)) or await check_status(callback):
                    print(True, "Without disscount")

                    buy_credits_inline = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=buy_credits, callback_data="pay_credits")]
                    ])

                    await callback.message.answer(
                    balance_not_enough_10 + f"<b>{user_credits}</b>",
                    parse_mode="HTML",
                    reply_markup=buy_credits_inline
                    )

                    await callback.answer()

                    if user_id in user_video_messages:
                        for msg_id in user_video_messages[user_id]:
                            try:
                                await bot.delete_message(chat_id=user_id, message_id=msg_id)
                            except Exception:
                                pass
                        del user_video_messages[user_id]
                    return
                else:
                    print(False, "With disscount")

                    buy_credits_inline = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=buy_credits, callback_data="pay_credits"),
                     InlineKeyboardButton(text=get_5_free_credits, callback_data="subscribe_to_channel")]
                    ])

                    await callback.message.answer(
                    balance_not_enough_10 + f"<b>{user_credits}</b>",
                    parse_mode="HTML",
                    reply_markup=buy_credits_inline
                    )

                    await callback.answer()

                    if user_id in user_video_messages:
                        for msg_id in user_video_messages[user_id]:
                            try:
                                await bot.delete_message(chat_id=user_id, message_id=msg_id)
                            except Exception:
                                pass
                        del user_video_messages[user_id]
                    return

                

            if not spend_credits(user_id, 10):
                await callback.message.answer(could_not_spend_credits)
                await callback.answer()
                return
            
            

            status_message = await callback.message.answer(
    process_time
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
                
                try:
                    os.remove(file_path)       
                except Exception as e:
                    print(f"Error while deleting: {e}")
                await callback.message.answer(error_processing_image + " Your credits have been refunded.")
                add_credits(user_id, 10)

        elif action == "process_video":

            relative_path = os.getenv("RELATIVE_PATH")

            media = [
                InputMediaVideo(media=FSInputFile(relative_path+ "/videos/undress_.mp4")),
                InputMediaVideo(media=FSInputFile(relative_path+ "/videos/clothe-off-trend.mp4")),
                InputMediaVideo(media=FSInputFile(relative_path+ "/videos/RIP_HER_CLOTH.mp4")),
                InputMediaVideo(media=FSInputFile(relative_path+ "/videos/touchboobies.mp4")),
                InputMediaVideo(media=FSInputFile(relative_path+ "/videos/TITTYDROP.mp4")),
                InputMediaVideo(media=FSInputFile(relative_path+ "/videos/breast_play.mp4")),
            ]

            sent_videos = await bot.send_media_group(chat_id=callback.from_user.id, media=media)
            user_video_messages[user_id] = [m.message_id for m in sent_videos]

            
            effects_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=effect_undress, callback_data=f"video_effect:effect1:{file_path}"), InlineKeyboardButton(text=effect_cloth_off_trend, callback_data=f"video_effect:effect2:{file_path}")],
                [InlineKeyboardButton(text=effect_rip_her_clothes, callback_data=f"video_effect:effect3:{file_path}"), InlineKeyboardButton(text=effect_touch_boobs, callback_data=f"video_effect:effect4:{file_path}")],
                [InlineKeyboardButton(text=effect_titty_drop, callback_data=f"video_effect:effect5:{file_path}"), InlineKeyboardButton(text=effect_breast_play, callback_data=f"video_effect:effect6:{file_path}")]
            ])
            await callback.message.answer(video_effect, reply_markup=effects_keyboard)

    @dp.callback_query(lambda c: c.data == "pay_credits")
    async def pay_credits_callback(callback: types.CallbackQuery, state: FSMContext):
        try:
            await callback.message.delete()
        except Exception:
            pass

        language = get_user_language(callback.from_user.id)
        choose_payment_method = get_text("choose_payment_method", language=language)

        await state.set_state(UserStates.BUY_CREDITS)
        await callback.message.answer(
            choose_payment_method,
            reply_markup=buy_credits_reply_menu(language)
        )
        await callback.answer()


    @dp.callback_query(lambda c: c.data.startswith("video_effect:"))
    async def process_video_effect(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        _, effect_name, file_path = callback.data.split(":", 2)

        try:
            await callback.message.delete()
        except Exception:
            pass

        language = get_user_language(callback.from_user.id)
        buy_credits = get_text("buy_credits", language=language)
        balance_not_enough_20 = get_text("balance_not_enough_20", language=language)
        could_not_spend_credits = get_text("could_not_spend_credits", language=language)
        process_3_4_minutes = get_text("process_3_4_minutes", language=language)
        error_processing_image = get_text("error_processing_image", language=language)

        user_credits = get_user_credits(user_id)
        if user_credits < 20:
                
                buy_credits_inline = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=buy_credits, callback_data="pay_credits")]
                ])

                await callback.message.answer(
                    balance_not_enough_20 + f"<b>{user_credits}</b>",
                    parse_mode="HTML",
                    reply_markup=buy_credits_inline
                )
                await callback.answer()

                if user_id in user_video_messages:
                    for msg_id in user_video_messages[user_id]:
                        try:
                            await bot.delete_message(chat_id=user_id, message_id=msg_id)
                        except Exception:
                            pass
                    del user_video_messages[user_id]
                return

        if not spend_credits(user_id, 20):
                await callback.message.answer(could_not_spend_credits)
                await callback.answer()
                return
                
        if user_id in user_video_messages:
            for msg_id in user_video_messages[user_id]:
                try:
                    await bot.delete_message(chat_id=user_id, message_id=msg_id)
                except Exception:
                    pass
            del user_video_messages[user_id]

        time_start = time.time()

        status_message = await callback.message.answer(process_3_4_minutes)
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
                await callback.message.answer(error_processing_image + " Your credits have been refunded.")
                try:
                    os.remove(file_path)       
                except Exception as e:
                    print(f"Error while deleting: {e}")
                add_credits(user_id, 20)
