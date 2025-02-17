# import discord

from discord.ext import commands

# from typing import Required, Optional


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check the bot's latency")
    async def utilities_ping(self, ctx):
        """Check the bot's latency"""
        await ctx.send(f"Pong! {self.bot.latency}")


async def setup(bot):
    await bot.add_cog(Utils(bot))
