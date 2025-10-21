import asyncio
import base64
import json
import os
import time
import aiohttp
import random
from dotenv import load_dotenv

load_dotenv()

API = os.getenv("API")
SERVER_ID = os.getenv("SERVER_ID")

URL_RUN = f"https://api.runpod.ai/v2/{SERVER_ID}/run"
URL_STATUS = f"https://api.runpod.ai/v2/{SERVER_ID}/status"

headers = {
    "Authorization": f"Bearer {API}",
    "Content-Type": "application/json"
}

with open("runpod/workflow_api.json", "r", encoding="utf-8") as f:
    workflow = json.load(f)


async def call_runpod_api(IMAGE_PATH, image_name, user_id=None):
    # читаем и кодируем картинку
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    img_data_uri = f"data:image/jpeg;base64,{img_b64}"

    workflow["35"]["inputs"]["image"] = image_name
    workflow["13"]["inputs"]["noise_seed"] = random.randint(1, 100000000)
    # workflow["19"]["inputs"]["steps"] = 40

    payload = {
        "input": {
            "workflow": workflow,
            "images": [
                {"name": image_name, "image": img_data_uri}
            ]
        }
    }

    print(f"User: {user_id} - Image {image_name} sent to runpod")
    time_start = time.time()

    timeout = aiohttp.ClientTimeout(total=600)  # увеличено до 10 минут
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # запускаем задачу
        async with session.post(URL_RUN, headers=headers, json=payload) as resp:
            start_data = await resp.json()
            job_id = start_data.get("id")
            if not job_id:
                print("Failed to get job_id:", start_data)
                return None

        # опрашиваем статус
        while True:
            async with session.get(f"{URL_STATUS}/{job_id}", headers=headers) as resp:
                status_data = await resp.json()
                status = status_data.get("status")

                if status == "COMPLETED":
                    images = status_data.get("output", {}).get("images", [])
                    if images:
                        img_obj = images[0]
                        img_data = img_obj.get("data")

                        if img_data:
                            img_bytes = base64.b64decode(img_data)
                            save_dir = os.path.dirname(IMAGE_PATH)
                            filename = os.path.join(save_dir, f"{os.path.splitext(image_name)[0]}_naked.png")

                            with open(filename, "wb") as f:
                                f.write(img_bytes)

                            time_end = time.time()
                            print(f"User: {user_id} - Response time: {time_end - time_start:.2f} seconds")
                            print(f"Saved file: {filename}")
                            return filename

                    print("No image data in response:", status_data)
                    return None

                elif status == "FAILED":
                    print("Job failed:", status_data)
                    return None

            # ждем 5 секунд между проверками
            await asyncio.sleep(5)


# if __name__ == "__main__":
#     IMAGE_PATH = "path/to/image.jpg"
#     image_name = "image.jpg"
#     asyncio.run(call_runpod_api(IMAGE_PATH, image_name))