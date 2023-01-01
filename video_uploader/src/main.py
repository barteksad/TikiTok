import pika
from fastapi import FastAPI, Response, File
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


@app.post("/upload/{title}")
def upload(response: Response, title: str, file: bytes = File()):
    """Uploads video with title `title` from `file` to BunnyCDN."""
    try:
        _, height, width, _ = iio.improps(file, plugin="pyav").shape
        metadata = iio.immeta(file, plugin="pyav")
    except Exception as error:
        logger.error(f"Cannot read video metadata: {error}")
        response.status_code = 400
        return {"message": "Invalid video format"}

    if metadata["duration"] > MAX_VIDEO_LENGTH:
        response.status_code = 400
        return {"message": "Video is too long."}
    if height > MAX_VIDEO_HEIGHT or width > MAX_VIDEO_HEIGHT:
        response.status_code = 400
        return {"message": "Video resolution is too large."}

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
