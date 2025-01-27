import discord

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from src.utils.checks import check_perms
from typing import Optional, List, Required


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        ctx,
        member: discord.Member,
        *,
        reason: Optional[str] = "No reason provided.",
    ):
        await member.ban(reason=reason)
        ban_embed = EmbedUtils.create_embed(
            title="Member Banned",
            description=f"🔨 | {member.mention} has been kicked for *{reason}*",
            color=discord.Color.green(),
        )
        await ctx.send(embed=ban_embed)

    @commands.hybrid_command(name="unban")  # TODO: complete this command
    @check_perms("ban_members")
    async def moderator_unban(self, ctx, *, user_id: int):
        pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
