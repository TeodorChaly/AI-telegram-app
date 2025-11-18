import json
import os
import random

import requests
from dotenv import load_dotenv

load_dotenv()

api_dock = os.getenv("API_AGE")
api_dock = json.loads(api_dock)


def detect_minor_file(image_path: str):
    random_id = random.choice(list(api_dock.keys()))
    print(random_id, api_dock[random_id])
    API_USER = random_id
    API_SECRET = api_dock[random_id]


    payload = {
        'models': 'face-age',
        'api_user': API_USER,
        'api_secret': API_SECRET
    }

    try:
        with open(image_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(
                'https://api.sightengine.com/1.0/check.json',
                data=payload,
                files=files
            )
      

    except Exception as e:
        print(f"Error during API request: {e}")
        return False
    
    data = response.json()

    if "faces" not in data or len(data["faces"]) == 0:
        return False

    results = []
    for face in data["faces"]:
        minor_prob = face["attributes"]["age"]["minor"]
        print(minor_prob)
        if minor_prob >= 0.5:
            return True



    return False

# print(detect_minor_file(
#     "https://instagram.frix8-1.fna.fbcdn.net/v/t51.29350-15/412199052_869009284698048_1104875682262562133_n.jpg?stp=dst-jpg_e35_p1080x1080_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0uaW1hZ2VfdXJsZ2VuLjE0NDB4MTgwMC5zZHIuZjI5MzUwLmRlZmF1bHRfaW1hZ2UuYzIifQ&_nc_ht=instagram.frix8-1.fna.fbcdn.net&_nc_cat=100&_nc_oc=Q6cZ2QEP75CITbIwQnyAxfsmiY_dSZeB7F0QJNrQpe6yvou_2bTC5IfXuBAyVY2QXFHoP8E&_nc_ohc=Dc6Bo27GIOgQ7kNvwGWkKoU&_nc_gid=x85l_Cri-H21Ml2dS2Q-og&edm=APoiHPcBAAAA&ccb=7-5&ig_cache_key=MzI2MTQzNzU3NTUyMjU1MDY2Ng%3D%3D.3-ccb7-5&oh=00_Afji07kcr6SOf3MCqOWom4XkH2TDGFkdEjLo7sfjfvUeAQ&oe=69211171&_nc_sid=22de04"
# ))