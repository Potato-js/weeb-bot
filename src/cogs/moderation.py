import asyncio

import discord

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from src.utils.checks import check_perms
from src.utils.utils import parse_duration
from typing import Optional, List, Required

logger = setup_logger()


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.parse_duration = parse_duration

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            missing_perms_embed = EmbedUtils.error_embed(
                description=f"⛔ | You do not have permission to {missing_perms}",
                title="Invalid Permissions",
            )
            await ctx.send(embed=missing_perms_embed)
        elif isinstance(error, commands.CheckFailure):
            missing_perms_embed = EmbedUtils.error_embed(
                description=f"⛔ | You do not have permission to run this command!",
                title="Invalid Permissions",
            )
            await ctx.send(embed=missing_perms_embed)
        else:
            raise error

    @commands.hybrid_command(name="kick")
    @check_perms("kick_members")
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
            description=f"🥾 | {member.mention} has been kicked from the server for *{reason}*.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=kick_embed)

    @commands.hybrid_command(name="ban")
    @check_perms("ban_members")
    async def moderator_ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        duration: Optional[str] = "30d",
        reason: Optional[str] = "No reason provided.",
    ):
        guild = ctx.guild
        duration_seconds = self.parse_duration(duration)
        if duration_seconds is None:
            err_embed = EmbedUtils.error_embed(
                "❗ | Invalid format. Use something like `12h` or `30d`"
            )
            await ctx.send(embed=err_embed)
            return

        await member.ban(reason=reason, delete_message_days=7)
        ban_embed = EmbedUtils.create_embed(
            title="Member Banned",
            description=f"🔨 | {member.mention} has been kicked for *{reason}* for **{duration}**",
            color=discord.Color.green(),
        )
        await ctx.send(embed=ban_embed)

        await asyncio.sleep(duration_seconds)
        try:
            await guild.unban(member, reason="Ban expired")
        except discord.NotFound:
            return

    @commands.hybrid_command(name="unban")
    @check_perms("ban_members")
    async def moderator_unban(
        self,
        ctx: commands.Context,
        *,
        user: discord.User,
        reason: Optional[str] = "No reason Provided",
    ):
        guild = ctx.guild

        await guild.unban(user=user, reason=reason)
        unban_embed = EmbedUtils.create_embed(
            title="Member Unbanned",
            description=f"✅ | {user.mention} has been unbanned!",
            color=discord.Color.green(),
        )
        await ctx.send(embed=unban_embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
