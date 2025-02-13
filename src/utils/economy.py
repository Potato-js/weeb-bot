import psycopg2

from dotenv import load_dotenv
from os import getenv

load_dotenv()
DB_NAME = getenv("DB_NAME")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")


class EconomyUtils:
    async def __init__(self):
        self.db_conn = {
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "host": DB_HOST,
            "port": DB_PORT,
        }

    async def setup_database(self):
        conn = psycopg2.connect(**self.db_conn)
        cursor = conn.cursor()
        await cursor.execute(
            "CREATE TABLE IF NOT EXISTS bank(wallet BIGINT, bank BIGINT, maxbank BIGINT, user BIGINT)"
        )
        await cursor.execute()
        await conn.close()

    async def create_wallet(self, user_id: int):
        pass
