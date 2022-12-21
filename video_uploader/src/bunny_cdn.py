import requests
from dotenv import load_dotenv
import os
from fastapi import File

# Env variables
load_dotenv()
API_KEY = os.environ['API_KEY']
VIDEO_LIB_ID = os.environ['VIDEO_LIB_ID']

URL = f'https://video.bunnycdn.com/library/{VIDEO_LIB_ID}/videos'


def create_video(title: str) -> requests.Response:
    """
    Creates new video object in BunnyCDN.
    :param title: title of the video.
    :return: response e.g. {"success":true,"message":"OK","statusCode":200}
    """
    payload = f'{{\"title\":\"{title}\"}}'
    headers = {
        "accept": "application/json",
        "content-type": "application/*+json",
        "AccessKey": API_KEY
    }
    response = requests.post(URL, data=payload, headers=headers)
    return response


def upload_video_from_file(video_id: int, video: File) -> requests.Response:
    """
    Reads video located at `video_path` and uploads it to BunnyCDN to object `video_id`.
    :param video:
    :param video_id: ID of the video object at BunnyCDN to store the video.
    :return: response e.g. {"success":true,"message":"OK","statusCode":200}
    """
    url = f'{URL}/{video_id}'
    headers = {
        "accept": "application/json",
        "content-type": "application/octet-stream",
        "AccessKey": API_KEY
    }
    return requests.put(url, data=video, headers=headers)


def delete_video(video_id: int):
    url = f'{URL}/{video_id}'
    headers = {
        "accept": "application/json",
        "AccessKey": API_KEY
    }
    return requests.delete(url, headers=headers)
