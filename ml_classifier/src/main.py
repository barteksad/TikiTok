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


def process_video(video_id: str):
    # Download the video from CDN.
    # TODO: get video object and check it's status (e.g. bunnyCDN encoding failed)
    # TODO: if video is OK, but not ready for download yet, sleep and try again later.
    response = cdn.download_video(video_id)
    if response.status_code != 200:
        cdn.delete_video(video_id)
        postgres.execute(
            r"""
            UPDATE video SET status = 'INVALID',
                             time_processed = %s
            WHERE id = %s
            """,
            (datetime.now(), video_id)
        )
    else:
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
    video_id = body.decode()
    print(" [x] Received %r" % body.decode())
    try:
        process_video(video_id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(e)


rabbitmq.queue_declare(queue='classifier_jobs', durable=True)
rabbitmq.basic_qos(prefetch_count=1)
rabbitmq.basic_consume(queue='classifier_jobs', on_message_callback=job_handler)
rabbitmq.start_consuming()

