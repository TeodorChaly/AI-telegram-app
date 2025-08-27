
import asyncio
import base64
import json
import os
import time

import aiohttp
import requests

from dotenv import load_dotenv
load_dotenv()

from logs import log_message

API = os.getenv("API")
server_id = os.getenv("SERVER_ID")


URL = f"https://api.runpod.ai/v2/{server_id}/runsync"

headers = {
    "Authorization": f"Bearer {API}",
    "Content-Type": "application/json"
}

with open("runpod/workflow_api.json", "r", encoding="utf-8") as f:
    workflow = json.load(f)


async def call_runpod_api(IMAGE_PATH, image_name, user_id=None):
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    img_data_uri = f"data:image/jpeg;base64,{img_b64}"

    workflow["35"]["inputs"]["image"] = image_name
    
    payload = {
        "input": {
            "workflow": workflow,
            "images": [
                {"name": image_name, "image": img_data_uri}
            ]
        }
    }
    timeout = aiohttp.ClientTimeout(total=300)
    await log_message(f"Image {image_name} sended to runpod", user_id)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(URL, headers=headers, json=payload, timeout=timeout) as resp:
                data = await resp.json()
        except Exception as e:
            await log_message(f"Crush error, {e}", user_id)
            return

    status = data.get("status", "UNKNOWN")

    if status in ("COMPLETED", "FAILED"):
        if status == "COMPLETED":
            images = data.get("output", {}).get("images", [])
            if images: 
                img_obj = images[0] 
                img_data = img_obj.get("data")
                if img_data:
                    img_bytes = base64.b64decode(img_data)

                    save_dir = os.path.dirname(IMAGE_PATH)
                    filename = os.path.join(save_dir, f"{os.path.splitext(image_name)[0]}_naked.png")
                    await log_message(f"Image {os.path.splitext(image_name)[0]}_naked.png processed", user_id)

                    with open(filename, "wb") as f:
                        f.write(img_bytes)

                    return filename
        else:
            await log_message(f"Out of time", user_id)
            return None


if __name__ == "__main__":
    IMAGE_PATH = ""
    image_name = ""

    asyncio.run(call_runpod_api(IMAGE_PATH, image_name))