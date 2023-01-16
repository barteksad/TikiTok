from typing import Union, List

import firebase_admin
from firebase_admin import auth
import pika
from fastapi import FastAPI, Response, File, Header
from fastapi.middleware.cors import CORSMiddleware
import logging

import src.bunny_cdn as cdn
import src.db as db
import src.job_queue as job_queue

import os
from dotenv import load_dotenv
import imageio.v3 as iio

load_dotenv()

# Logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("requests.packages.urllib3")
logger.setLevel(logging.INFO)
logger.propagate = True

app = FastAPI()
# GOOGLE_APPLICATION_CREDENTIALS env variable must be a path to firebase admin .json file.
firebase = firebase_admin.initialize_app()

# CORS setup
origins = [os.environ["DOMAIN"]]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

postgres_conn = db.connect()
postgres_conn.autocommit = False
postgres = postgres_conn.cursor()

rabbitmq_conn = job_queue.connect()
rabbitmq = rabbitmq_conn.channel()
rabbitmq.queue_declare(queue='classifier_jobs', durable=True)

MAX_VIDEO_LENGTH = 15  # in seconds.
MAX_VIDEO_HEIGHT = 720
MAX_VIDEO_WIDTH = 1280


def check_id_token(token: str):
    token = token.removeprefix("Bearer ")
    return auth.verify_id_token(token)


def check_video(file: bytes):
    try:
        _, height, width, _ = iio.improps(file, plugin="pyav").shape
        metadata = iio.immeta(file, plugin="pyav")
    except Exception as error:
        logger.error(f"Cannot read video metadata: {error}")
        raise AssertionError("Invalid video format.")

    if metadata["duration"] > MAX_VIDEO_LENGTH:
        raise AssertionError("Video is too long.")
    if height > MAX_VIDEO_HEIGHT or width > MAX_VIDEO_WIDTH:
        raise AssertionError("Video resolution is too large.")


@app.post("/upload/{title}")
def upload(response: Response, title: str, file: bytes = File(),
           authorization: Union[str, None] = Header(default=None)):
    """Uploads video with title `title` from `file` to BunnyCDN."""
    try:
        user = check_id_token(authorization)
    except Exception as error:
        logger.error(f"Cannot verify token {authorization}. Reason: {error}.")
        response.status_code = 403
        return {"message": f"Invalid ID token."}

    logger.info(f"Successfully authorized user {user['user_id']} {user['email']}.")

    try:
        check_video(file)
    except Exception as error:
        logger.error(f"Cannot process video: {error}.")
        response.status_code = 400
        return {"message": error}

    resp1 = cdn.create_video(title)
    response.status_code = resp1.status_code
    if resp1.status_code != 200:
        return {"message": resp1.json()}
    video_id = resp1.json()['guid']
    logger.info(f'Created a video object: \n {resp1.json()}')

    try:
        resp2 = cdn.upload_video_from_file(video_id, file)
        response.status_code = resp2.status_code
        if resp2.status_code != 200:
            raise IOError(f'Failed to upload contents of video {video_id} to CDN: {resp2.json()}')
        logger.info(f'Uploaded the video: \n {resp2.json()}')

        postgres.execute(r'INSERT INTO video(id, title) VALUES (%s, %s);', (video_id, title))
        logger.info(f"Created a record for video's {video_id} metadata.")

        rabbitmq.basic_publish(exchange='',
                               routing_key='classifier_jobs',
                               body=f'{video_id}',
                               properties=pika.BasicProperties(
                                   delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                               ))
        logger.info(f"Pushed video ID {video_id} to the processing queue.")

        postgres_conn.commit()
        return resp2.json()
    except Exception as error:
        postgres_conn.rollback()
        cdn.delete_video(video_id)
        logger.error(f"ROLLBACK: {error}")
        response.status_code = 500
        return {"message": error}
