import requests
from dotenv import load_dotenv
import os

# Env variables
load_dotenv()

API_KEY = os.environ['API_KEY']
VIDEO_LIB_ID = os.environ['VIDEO_LIB_ID']
BUNNY_CND_PULL_ZONE = os.environ['BUNNY_CND_PULL_ZONE']
URL = f'https://video.bunnycdn.com/library/{VIDEO_LIB_ID}/videos'


def download_video(video_id: str) -> requests.Response:
    url = f"https://{BUNNY_CND_PULL_ZONE}.b-cdn.net/{video_id}/play_240p.mp4"
    print(url)
    return requests.get(url)

def delete_video(video_id: str):
    url = f'{URL}/{video_id}'
    headers = {
        "accept": "application/json",
        "AccessKey": API_KEY
    }
    return requests.delete(url, headers=headers)


def get_video_object(video_id: str) -> requests.Response:
    url = f'{URL}/{video_id}'
    headers = {
        "accept": "application/json",
        "AccessKey": API_KEY
    }
    response = requests.get(url, headers=headers)
    return response
