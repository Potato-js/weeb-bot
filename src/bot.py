import discord
import os

from discord.ext import commands
from dotenv import load_dotenv
from src.utils.logger import setup_logger
from src.utils.economy import EconomyUtils

load_dotenv()
PREFIX = os.getenv("PREFIX")
GUILD_ID = os.getenv("GUILD_ENV")

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
    activity = discord.Streaming(name=f"{PREFIX}help", url="https://twitch.tv/insane1y")
    logger.info(f"Client {bot.user} is ready")
    synced = await bot.tree.sync(guild=GUILD_ID)
    print(f"Synced {len(synced)} command(s)")
    await EconomyUtils.setup_database()
    await bot.change_presence(activity=activity)


async def login(token):
    await load_cogs()
    await bot.start(token)
