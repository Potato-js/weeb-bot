import discord

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from typing import Optional, List, Required


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(
        self,
        ctx,
        member: discord.Member,
        *,
        reason: Optional[str] = "No reason provided.",
    ):
        await member.kick(reason=reason)
        kick_embed = EmbedUtils.create_embed(
            title="Member Kicked",
            description=f"{member.mention} has been kicked from the server for *{reason}*.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=kick_embed(member, reason))


async def setup(bot):
    await bot.add_cog(Moderation(bot))
