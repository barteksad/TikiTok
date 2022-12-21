import os

import pika
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def connect():
    try:
        print('Connecting to the RabbitMQ message broker...')
        rabbit_credentials = pika.PlainCredentials(os.environ["RABBIT_MQ_USER"], os.environ["RABBIT_MQ_PASSWORD"])
        rabbit_params = pika.ConnectionParameters(os.environ["RABBIT_MQ_HOST"],
                                                  int(os.environ["RABBIT_MQ_PORT"]),
                                                  os.environ["RABBIT_MQ_ROUTE"],
                                                  rabbit_credentials)
        return pika.BlockingConnection(rabbit_params)
    except Exception as error:
        print(error)
        exit(1)

