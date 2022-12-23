import os

import pika
from dotenv import load_dotenv

load_dotenv()


def connect():
    try:
        print('Connecting to the RabbitMQ message broker...')
        rabbit_credentials = pika.PlainCredentials(username=os.environ["RABBIT_MQ_USER"],
                                                   password=os.environ["RABBIT_MQ_PASSWORD"])
        rabbit_params = pika.ConnectionParameters(host=os.environ["RABBIT_MQ_HOST"],
                                                  port=int(os.environ["RABBIT_MQ_PORT"]),
                                                  virtual_host=os.environ["RABBIT_MQ_ROUTE"],
                                                  credentials=rabbit_credentials,
                                                  heartbeat=0)
        return pika.BlockingConnection(rabbit_params)
    except Exception as error:
        print(error)
        exit(1)

