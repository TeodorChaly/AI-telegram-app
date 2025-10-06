
import asyncio
from typing import Any, Dict, Optional
import json
import asyncio
import os
from aiogram import Bot
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.types import FSInputFile,InputMediaPhoto
import sys

load_dotenv()


API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")


async def send_to_user(bot, chat_id):

    attempt = 0
    max_retries = 5

    while attempt <= max_retries:
        try:
            relative_path = os.getenv("RELATIVE_PATH")

            from aiogram.types import FSInputFile,InputMediaPhoto
            
            photo1 = FSInputFile(relative_path + "videos/girl1.jpg")
            photo2 = FSInputFile(relative_path + "videos/girl2.jpg")

            media = [
                InputMediaPhoto(media=photo1, caption="""🔞 It's time to undress me - upload a photo for see me without cloth!
Try and see for yourself 👇""", parse_mode="HTML"),
                InputMediaPhoto(media=photo2)
            ]

            await bot.send_media_group(chat_id=chat_id, media=media)


            return {"ok": True}
        except Exception as e:
            print(f"Error: {e}")
            attempt += 1
                 
    return {"ok": False}





async def run_production(bot):
    with open("credits.json", "r") as f:
        data = json.load(f)

    chat_ids = [int(cid) for cid in data.keys()]

    for chat_id in chat_ids:
        print(chat_id)
        result = await send_to_user(bot, chat_id)
        if result["ok"]:
            print(f"Sent to {chat_id}.")
        else:
            print(f"Failed to {chat_id}")



async def test_message(bot):
    chat_ids = os.getenv("TEST_USERS", "")
    chat_ids = [cid.strip() for cid in chat_ids.split(",") if cid.strip()]

    
    with open("credits.json", "r") as f:
        data = json.load(f)

    print("Production users will be sended:", len(data))

    for chat_id in chat_ids:
        print(chat_id)
        result = await send_to_user(bot, chat_id)
        if result["ok"]:
            print(f"Sent to {chat_id}.")
        else:
            print(f"Failed to {chat_id}")



async def main():
    bot = Bot(token=API_TOKEN)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Testing...")
        await test_message(bot)
    else:
        print("Production...")
        await run_production(bot)

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())