import discord

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import *
from typing import Optional, List, Required


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Moderation(bot))
