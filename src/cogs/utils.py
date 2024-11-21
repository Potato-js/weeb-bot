# import discord

from discord.ext import commands


class Utils(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"Pong! {self.bot.latency}")


async def setup(bot):
    await bot.add_cog(Utils(bot))
