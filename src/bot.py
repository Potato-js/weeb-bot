import discord
import os

from discord.ext import commands
from src.utils.logger import setup_logger

logger = setup_logger()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


async def load_cogs():
    for fn in os.listdir("./src/cogs"):
        if fn.endswith(".py"):
            cog = f"src.cogs.{fn[:-3]}"
            try:
                await bot.load_extension(cog)
                logger.info(f"Loaded {cog}")
            except Exception as e:
                logger.warning(f"Failed to load {cog} \n{e}")


@bot.event
async def on_ready():
    logger.info(f"Client {bot.user} is ready")


async def login(token):
    await load_cogs()
    await bot.start(token)
