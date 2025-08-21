import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from aiogram.fsm.context import FSMContext
from function import *

from fsm_states import UserStates
from runpod.call_runpod import call_runpod_api 
from keyboards import main_menu, send_photo_menu, buy_credits_menu


async def send_user_agreement(message: types.Message):
    await message.answer(
        "📜 *User Agreement*\n\n" +
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        reply_markup=get_user_agreement_keyboard(),
        parse_mode="Markdown"
    )

def register_handlers(dp: Dispatcher, bot: Bot):

    @dp.message(Command("start"))
    async def start_handler(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if is_user_agreed(user_id):
            await state.set_state(UserStates.MAIN_MENU)
            await message.answer("Welcome back! Choose an option:", reply_markup=main_menu)
        else:
            await send_user_agreement(message)

    @dp.callback_query(lambda c: c.data == "agree")
    async def on_agree(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        user_agreed.add(user_id)
        save_agreed_users(user_agreed)
        await state.set_state(UserStates.MAIN_MENU)
        await callback.message.edit_text("You agreed! ✅")
        await callback.message.answer("Choose an option:", reply_markup=main_menu)
        await callback.answer()

    @dp.message()
    async def global_handler(message: types.Message, state: FSMContext):
        user_id = message.from_user.id


        if not is_user_agreed(user_id):
            await send_user_agreement(message)
            return

        current_state = await state.get_state()
        if current_state is None:
            current_state = UserStates.MAIN_MENU.state

        if message.text == "💰 Show my credits" and current_state == UserStates.BUY_CREDITS.state:
            user_credits = get_user_credits(user_id)
            await message.answer(f"💰 You have {user_credits} credits.")
            return

        if message.text == "🛒 Buy credits" and current_state == UserStates.BUY_CREDITS.state:
            add_credits(user_id, 10)
            user_credits = get_user_credits(user_id)
            await message.answer(f"🛒 You bought 10 credits! Now you have {user_credits} credits.")
            return

        current_state = await state.get_state()
        if current_state is None:
            current_state = UserStates.MAIN_MENU.state

        if message.text == "📸 Send photo":
            await state.set_state(UserStates.SEND_PHOTO)
            await message.answer("Please upload a photo and I'll process it.", reply_markup=send_photo_menu)
            return

        if message.text == "💳 Buy credits":
            await state.set_state(UserStates.BUY_CREDITS)
            await message.answer("Select an option:", reply_markup=buy_credits_menu)
            return

        if message.text == "🛒 Buy credits" and current_state == UserStates.BUY_CREDITS.state:
            await message.answer("🛒 Buying credits... (placeholder)")
            return

        if message.text == "💰 Show my credits" and current_state == UserStates.BUY_CREDITS.state:
            await message.answer("💰 You have 0 credits. (placeholder)")
            return

        if message.text == "⬅️ Back to menu":
            await state.set_state(UserStates.MAIN_MENU)
            await message.answer("Back to main menu:", reply_markup=main_menu)
            return

        if message.text == "🌐 Language":
            await message.answer("🌐 Language selection coming soon!")
            return

        if message.text == "👤 Profile":
            await message.answer("👤 Profile section coming soon!")
            return

        if message.photo:
            if current_state == UserStates.SEND_PHOTO.state:
                user_credits = get_user_credits(user_id)
                if user_credits < 10:
                    await message.answer("⚠️ You don't have enough credits (10 required) to process the photo. Please buy credits.")
                    return

                success = spend_credits(user_id, 10)
                if not success:
                    await message.answer("⚠️ Could not spend credits. Try again later.")
                    return

                await message.answer("✅ Got your photo. Processing... 10 credits spent.")
                file_path = await save_photo(message, bot)

                file_full_path = os.path.abspath(file_path)
                file_name = file_path.replace("photos/", "")

                processed_image = await call_runpod_api(IMAGE_PATH=file_full_path, image_name=file_name, user_id=user_id)

                if processed_image is None:
                    await message.answer("❌ Error processing the image. Please try again later.")
                    return

                # Path to blurred image
                blured_image = await blur_image(processed_image)

                file_send_2 = FSInputFile(blured_image)
                await bot.send_photo(chat_id=message.chat.id, photo=file_send_2, caption="Here is your blured image!")
                os.remove(blured_image)


                file_send = FSInputFile(processed_image)
                await bot.send_photo(chat_id=message.chat.id, photo=file_send, caption="Here is your image!")


                return
            else:
                await message.answer("⚠️ Photo processing is only available in the 'Send photo' section.")
                return

        await message.answer("❓ Unknown command or input. Please choose from the menu.")
