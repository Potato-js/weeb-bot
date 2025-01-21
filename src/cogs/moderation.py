import discord

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from typing import Optional, List, Required


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: Make this work with fakeperms
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def moderator_kick(
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
        await ctx.send(embed=kick_embed)

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def moderator_ban(self, ctx, member: discord.Member, *, reason: Optional[str] = "No reason provided."):
        await member.ban(reason=reason)
        ban_embed = EmbedUtils.create_embed(
            title="Member Banned",
            description=f"{member.mention} has been kicked for *{reason}*",
            color=discord.Color.red(),
        )
        await ctx.send(embed=ban_embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
