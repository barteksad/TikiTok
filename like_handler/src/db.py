import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def connect():
    """ Connect to the PostgreSQL database server """
    try:
        # read connection parameters
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        return psycopg2.connect(
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=os.environ["DB_PORT"],
        )
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        exit(1)
