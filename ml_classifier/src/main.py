import time

import bunny_cdn as cdn
import db as db
import job_queue as job_queue
import video_processor as ML
from datetime import datetime

postgres_conn = db.connect()
postgres_conn.autocommit = False
postgres = postgres_conn.cursor()

rabbitmq_conn = job_queue.connect()
rabbitmq = rabbitmq_conn.channel()

VID_CREATED = 0
VID_UPLOADED = 1
VID_PROCESSING = 2
VID_TRANSCODING = 3
VID_FINISHED = 4
VID_ERROR = 5
VID_UPLOAD_FAILED = 6

DEFAULT_BACKOFF = 4
BACKOFF_MULTIPLIER = 2
MAX_BACKOFF = 1 << 10
backoff = 4  # Time to wait on error.


def process_video(video_id: str):
    # Download the video from CDN.
    response = cdn.get_video_object(video_id)

    if response.status_code != 200:
        raise IOError(f'Getting video metadata failed: {response.status_code} {response.json()}')

    print(response)
    status = response.json()['status']
    if status == VID_ERROR or status == VID_UPLOAD_FAILED:
        cdn.delete_video(video_id)
        postgres.execute(
            r"""
            UPDATE video SET status = 'INVALID',
                             time_processed = %s
            WHERE id = %s
            """,
            (datetime.now(), video_id)
        )
    elif (status == VID_CREATED
          or status == VID_UPLOADED
          or status == VID_PROCESSING
          or status == VID_TRANSCODING):
        raise IOError("Latest video is not ready yet.")
    else:  # status == VID_FINISHED
        response = cdn.download_video(video_id)
        print(response)
        if response.status_code != 200:
            raise IOError(f'Downloading video failed: {response.status_code} {response.json()}')
        raw_video_bytes = response.content
        classes = ML.process_video(video_id, raw_video_bytes)

        postgres.execute(
            r"""
            UPDATE video SET status = 'PROCESSED',
                             time_processed = %s,
                             class1 = %s,
                             class2 = %s,
                             class3 = %s
            WHERE id = %s
            """,
            (datetime.now(), classes[0].item(), classes[1].item(), classes[2].item(), video_id)
        )
    postgres_conn.commit()


def job_handler(ch, method, properties, body):
    global backoff
    video_id = body.decode()
    print(" [x] Received %r" % body.decode())
    try:
        process_video(video_id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        backoff = DEFAULT_BACKOFF  # reset
    except Exception as e:
        backoff *= BACKOFF_MULTIPLIER
        backoff = min(backoff, MAX_BACKOFF)
        print(f"ERROR {e}. Sleeping for {backoff}s.")
        ch.basic_nack(delivery_tag=method.delivery_tag)
        time.sleep(backoff)


rabbitmq.queue_declare(queue='classifier_jobs', durable=True)
rabbitmq.basic_qos(prefetch_count=1)
rabbitmq.basic_consume(queue='classifier_jobs', on_message_callback=job_handler)
rabbitmq.start_consuming()
