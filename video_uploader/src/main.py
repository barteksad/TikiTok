import pika
from fastapi import FastAPI, Response, File
import logging

import src.bunny_cdn as cdn
import src.db as db
import src.job_queue as job_queue

# Logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("requests.packages.urllib3")
logger.setLevel(logging.INFO)
logger.propagate = True

app = FastAPI()

postgres_conn = db.connect()
postgres_conn.autocommit = False
postgres = postgres_conn.cursor()

rabbitmq_conn = job_queue.connect()
rabbitmq = rabbitmq_conn.channel()
# rabbitmq.queue_declare(queue='classifier_jobs', durable=True)
rabbitmq.queue_declare(queue='classifier_jobs', durable=True)

@app.post("/upload/{title}")
def upload(response: Response, title: str, file: bytes = File()):
    """Uploads video with title `title` from `file` to BunnyCDN."""

    resp1 = cdn.create_video(title)
    response.body = resp1.json()
    response.status_code = resp1.status_code
    if resp1.status_code != 200:
        return
    video_id = resp1.json()['guid']
    logger.info(f'Created a video object: \n {resp1.json()}')

    try:
        resp2 = cdn.upload_video_from_file(video_id, file)
        response.body = resp1.json()
        response.status_code = resp2.status_code
        if resp2.status_code != 200:
            raise IOError(f'Failed to upload contents of video {video_id} to CDN.')
        logger.info(f'Uploaded the video: \n {resp2.json()}')

        postgres.execute(r'INSERT INTO video(id, title) VALUES (%s, %s);', (video_id, title))
        logger.info(f"Created a record for video's {video_id} metadata.")

        logger.info(f"Pushed video ID {video_id} to the processing queue.")

        postgres_conn.commit()

        rabbitmq.basic_publish(exchange='',
                               routing_key='classifier_jobs',
                               body=f'{video_id}',
                               properties=pika.BasicProperties(
                                   delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                               ))
    except Exception as error:
        postgres_conn.rollback()
        logger.error(error)
        response.status_code = 500
        cdn.delete_video(video_id)


