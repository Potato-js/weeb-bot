import discord
import os

from discord.ext import commands
from dotenv import load_dotenv
from src.utils.logger import setup_logger

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
            if cog == "src.cogs.__init__":
                return
            else:
                try:
                    await bot.load_extension(cog)
                    logger.info(f"Loaded {cog}")
                except Exception as e:
                    logger.warning(f"Failed to load {cog} \n{e}")


@bot.event
async def on_ready():
    logger.info(f"Client {bot.user} is ready")
    synced = (
        await bot.tree.sync(guild=GUILD_ID)
        if GUILD_ID is not None
        else await bot.tree.sync()
    )
    print(f"Synced {len(synced)} command(s)")


@bot.event
async def on_connect():
    activity = discord.Streaming(name=f"{PREFIX}help", url="https://twitch.tv/insane1y")
    await bot.change_presence(activity=activity)


async def login(token):
    await load_cogs()
    await bot.start(token)
