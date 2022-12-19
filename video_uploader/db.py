import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_USERNAME = os.environ['DB_USERNAME']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']


def connect():
    """ Connect to the PostgreSQL database server """
    try:
        # read connection parameters

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        return psycopg2.connect("postgresql://postgres:5432@localhost:5432/postgres")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


def read_query(cur, query, params = ()):
    cur.execute(query, params)
    return cur.fetchall()

def write_query(cur, query, params = ()):
    cur.execute(query, params)