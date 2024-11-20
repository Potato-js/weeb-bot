# import asyncio

from dotenv import load_dotenv
from os import getenv
from src.bot import login


if __name__ == "__main__":
    load_dotenv()
    token = getenv("TOKEN")
    login(token)
