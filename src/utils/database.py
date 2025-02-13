import psycopg

from dotenv import load_dotenv
from os import getenv

load_dotenv()
DB_NAME = getenv("DB_NAME")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")


class DatabaseUtils:
    async def __init__(self):
        self.db_conn = {
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "host": DB_HOST,
            "port": DB_PORT,
        }

    async def create_connection(self):
        conn = psycopg.connect(**self.db_conn)
        conn.cursor()
