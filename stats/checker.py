import os
import asyncio
import json
import sys
from dotenv import load_dotenv
from pathlib import Path
import requests
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from google_sheets import *

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

NOTIFICATION_TOKEN = os.getenv("NOTIFICATION_TOKEN")
NOTIFICATION_CHANNEL_ID = os.getenv("NOTIFICATION_CHANNEL_ID")

TG_BOT_NAME = os.getenv("BOT_NAME")

BASE_DIR = Path(__file__).parent 
file_path = BASE_DIR / "stats.json"

file_structure = {
        "new_users_today":0,
        "subscribed":0,
        "sended_photo":0,
        "sended_video":0,
        "processing_time":0,
        "look_to_buy":0,
        "look_to_buy_stars":0,
        "look_to_buy_crypto":0,
        "bought_stars":0,
        "bought_crypto":0,
        "amount_stars":0,
        "amount_crypto":0.0,
        "language":0
    }

async def check_stats():
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(file_structure, f) 
    

async def add_value(value_name, amount=1):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if value_name in data:
        data[value_name] += amount
    else:
        raise KeyError(f"No '{value_name}' field in stats.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


async def main():
    await check_stats()
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    await process_data(data)

    with open(file_path, "w") as f:
        json.dump(file_structure, f) 
    pass
    # await add_value("new_users_today")


async def process_data(data):
    today = datetime.today().strftime("%d.%m.%Y")  
    if data["new_users_today"] != 0:
        conversion_rate = ((data["bought_stars"] + data["bought_crypto"])/data["new_users_today"])
        conversion_rate_rounded = round(conversion_rate, 2)
        conversion_rate_rounded = conversion_rate_rounded * 100
    else:
        conversion_rate_rounded = 0



    total_usd = await get_total_sum_for_date(today)

        
    text_of_message = f"""
From {TG_BOT_NAME}

Stats for {today}
Total earned: {total_usd}
New users: {data["new_users_today"]},
Total subscribed to channel: {data["subscribed"]},
Total photo sended: {data["sended_photo"]},
Total video sended: {data["sended_video"]}
Total processing time: {data["processing_time"]},


People want to see pricing: {data["look_to_buy"]},
People that choose stars: {data["look_to_buy_stars"]},
People that choose crypto: {data["look_to_buy_crypto"]},
Bought stars: {data["bought_stars"]},
Bought crypto: {data["bought_crypto"]},
Bought stars (amount): {data["amount_stars"]},
Bought crypto (amount): {data["amount_crypto"]},
Wanted to change language: {data["language"]}

Conversion rate - {conversion_rate_rounded}%
"""
    await send_message(text_of_message)

async def send_message(text):
    print(text)
    url = f"https://api.telegram.org/bot{NOTIFICATION_TOKEN}/sendMessage"
    payload = {"chat_id": NOTIFICATION_CHANNEL_ID, "text": str(text)}
    requests.post(url, data=payload)



async def purchase_notification(money):

    url = f"https://api.telegram.org/bot{NOTIFICATION_TOKEN}/sendMessage"
    payload = {"chat_id": NOTIFICATION_CHANNEL_ID, "text": str(money)}
    requests.post(url, data=payload)



if __name__ == "__main__":
    asyncio.run(main())

