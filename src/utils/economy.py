import psycopg

from dotenv import load_dotenv
from os import getenv

load_dotenv()
DB_NAME = getenv("DB_NAME")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")


class EconomyUtils:
    db_conn = {
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "host": DB_HOST,
        "port": DB_PORT,
    }

    @classmethod
    def setup_database(cls):
        conn = psycopg.connect(**cls.db_conn)
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS bank(user_id BIGINT PRIMARY KEY, wallet BIGINT, bank BIGINT, maxbank BIGINT)"
        )
        conn.commit()
        cursor.close()
        conn.close()

    @classmethod
    def create_wallet(cls, user_id: int):
        conn = psycopg.connect(**cls.db_conn)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bank VALUES(%s, %s, %s, %s)", (user_id, 0, 100, 25000)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return

    @classmethod
    def get_balance(cls, user_id: int):
        conn = psycopg.connect(**cls.db_conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT wallet, bank, maxbank FROM bank WHERE user_id = %s", (user_id,)
        )
        data = cursor.fetchone()
        if data is None:
            cls.create_wallet(user_id)
            return 0, 100, 25000
        wallet, bank, maxbank = data[0], data[1], data[2]
        cursor.close()
        conn.close()
        return wallet, bank, maxbank

    @classmethod
    def update_wallet(cls, user_id: int, amount: int):
        conn = psycopg.connect(**cls.db_conn)
        cursor = conn.cursor()
        cursor.execute("SELECT wallet FROM bank WHERE user_id = %s", (user_id,))
        data = cursor.fetchone()
        if data is None:
            cls.create_wallet(user_id)
            return 0
        cursor.execute(
            "UPDATE bank SET wallet = %s WHERE user_id = %s",
            (data[0] + amount, user_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
