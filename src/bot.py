import discord
import os

from discord.ext import commands
from dotenv import load_dotenv
from src.utils.logger import setup_logger

load_dotenv()
PREFIX = os.getenv("PREFIX")

logger = setup_logger()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)


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
    # Change if you want your own twitch
    activity = discord.Streaming(name="!help", url="https://twitch.tv/insane1y")
    logger.info(f"Client {bot.user} is ready")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")
    await bot.change_presence(activity=activity)


async def login(token):
    await load_cogs()
    await bot.start(token)
