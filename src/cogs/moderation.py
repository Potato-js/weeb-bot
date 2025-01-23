import discord

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from typing import Optional, List, Required


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_fake_perms(self, ctx, perm_name: str) -> bool:
        """Check if a user has a fake permission."""
        fakeperms_cog = self.bot.get_cog("FakePerms")
        if not fakeperms_cog:
            return False  # FakePerms cog not loaded

        role_ids = [role.id for role in ctx.author.roles]

        for role_id in role_ids:
            role_perms = fakeperms_cog.get_role_permissions(role_id)
            perm_flag = fakeperms_cog.permission_flags.get(perm_name.upper())
            if perm_flag and (role_perms & perm_flag):
                return True

        return False

    # TODO: Make this work with fakeperms
    @commands.hybrid_command(name="kick")
    async def moderator_kick(
        self,
        ctx,
        member: discord.Member,
        *,
        reason: Optional[str] = "No reason provided.",
    ):
        if not (
            ctx.author.guild_permissions.kick_members
            or self.has_fake_perms(ctx, "KICK_MEMBERS")
        ):
            kick_embed = EmbedUtils.error_embed(
                "⛔ | You do not have permission to kick members."
            )
            return await ctx.send(embed=kick_embed)

        await member.kick(reason=reason)
        kick_embed = EmbedUtils.create_embed(
            title="Member Kicked",
            description=f"🥾 | {member.mention} has been kicked from the server for *{reason}*.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=kick_embed)

    @commands.hybrid_command(name="ban")
    async def moderator_ban(
        self,
        ctx,
        member: discord.Member,
        *,
        reason: Optional[str] = "No reason provided.",
    ):

        if not (
            ctx.author.guild_permissions.ban_members
            or self.has_fake_perms(ctx, "BAN_MEMBERS")
        ):
            kick_embed = EmbedUtils.error_embed(
                "⛔ | You do not have permission to ban members."
            )
            return await ctx.send(embed=kick_embed)

        await member.ban(reason=reason)
        ban_embed = EmbedUtils.create_embed(
            title="Member Banned",
            description=f"🔨 | {member.mention} has been kicked for *{reason}*",
            color=discord.Color.green(),
        )
        await ctx.send(embed=ban_embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
