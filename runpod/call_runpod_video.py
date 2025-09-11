import asyncio
import base64
import json
import os
import time
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API = os.getenv("API_VIDEO")
server_id = os.getenv("SERVER_ID_VIDEO")


URL_RUN = f"https://api.runpod.ai/v2/{server_id}/run"
URL_STATUS = f"https://api.runpod.ai/v2/{server_id}/status"

headers = {
    "Authorization": f"Bearer {API}",
    "Content-Type": "application/json"
}

with open("runpod/workflow_api_video.json", "r", encoding="utf-8") as f:
    workflow = json.load(f)


async def call_runpod_api_video(IMAGE_PATH, image_name, user_id=None):
    print(API, server_id)
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    img_data_uri = f"data:image/jpeg;base64,{img_b64}"

    workflow["122"]["inputs"]["image"] = image_name
    
    payload = {
        "input": {
            "workflow": workflow,
            "images": [
                {"name": image_name, "image": img_data_uri}
            ]
        }
    }

    print("User:", user_id, f"- Image {image_name} sent to runpod")
    time_start = time.time()

    timeout = aiohttp.ClientTimeout(total=400) 
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(URL_RUN, headers=headers, json=payload) as resp:
            start_data = await resp.json()
            job_id = start_data.get("id")
            if not job_id:
                print("Did't get job_id:", start_data)
                return None

        while True:
            async with session.get(f"{URL_STATUS}/{job_id}", headers=headers) as resp:
                status_data = await resp.json()
                status = status_data.get("status")

                if status == "COMPLETED":
                    images = status_data.get("output", {}).get("images", [])
                    if images:
                        for img_obj in images:
                            data_b64 = img_obj.get("data")
                            file_type = img_obj.get("type")
                            filename = img_obj.get("filename")

                            if not data_b64 or not filename:
                                continue

                            if file_type == "video_base64":
                                ext = ".mp4"
                            else:
                                ext = ".png"

                            save_dir = os.path.dirname(IMAGE_PATH)
                            out_path = os.path.join(save_dir, filename if filename else f"{os.path.splitext(image_name)[0]}{ext}")

                            with open(out_path, "wb") as f:
                                f.write(base64.b64decode(data_b64))

                            time_end = time.time()
                            print(f"User: {user_id} - Response time: {time_end - time_start:.2f} seconds")
                            print(f"Saved file: {out_path}")
                            return out_path

                    return None

                elif status == "FAILED":
                    print("Job failed:", status_data)
                    return None

            await asyncio.sleep(5)  


# if __name__ == "__main__":
#     IMAGE_PATH = ""
#     image_name = ""
#     asyncio.run(call_runpod_api(IMAGE_PATH, image_name))