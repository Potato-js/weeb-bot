import asyncio

from datetime import timedelta
from typing import Optional

import discord

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from src.utils.checks import check_perms
from src.utils.utils import parse_duration

logger = setup_logger()


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.parse_duration = parse_duration

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            missing_perms_embed = EmbedUtils.error_embed(
                description=f"""
                ⛔ | You do not have permission to {missing_perms}
                """,
                title="Invalid Permissions",
            )
            await ctx.send(embed=missing_perms_embed)
        elif isinstance(error, commands.CheckFailure):
            missing_perms_embed = EmbedUtils.error_embed(
                description="""
                ⛔ | You do not have permission to run this command!
                """,
                title="Invalid Permissions",
            )
            await ctx.send(embed=missing_perms_embed)
        else:
            raise error

    @commands.hybrid_command(name="kick")
    @check_perms("kick_members")
    async def moderator_kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: Optional[str] = "No reason provided.",
    ):
        """Kicks a specified member (Requires KICK_MEMBERS)"""
        await member.kick(reason=reason)
        kick_embed = EmbedUtils.create_embed(
            title="Member Kicked",
            description=f"🥾 | {member.mention} has been kicked for *{reason}*",
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
        duration: Optional[str] = "1d",
        reason: Optional[str] = "No reason provided.",
    ):
        """Bans a specified member (Requires BAN_MEMBERS)"""
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
            description=f"""
            🔨 | {member.mention} has been banned for *{reason}* for {duration}
            """,
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
        """Unbans a specified member (Requires BAN_MEMBERS)"""
        guild = ctx.guild

        await guild.unban(user=user, reason=reason)
        unban_embed = EmbedUtils.create_embed(
            title="Member Unbanned",
            description=f"✅ | {user.mention} has been unbanned!",
            color=discord.Color.green(),
        )
        await ctx.send(embed=unban_embed)

    @commands.hybrid_command(name="mute", aliases=["timeout"])
    @check_perms("moderate_members")
    async def moderator_mute_or_timeout(
        self,
        ctx: commands.Context,
        user: discord.Member,
        duration: Optional[str] = "3h",
        *,
        reason: Optional[str] = "No reason provided",
    ):
        """Timeouts/mutes a specified member (Requires MODERATE_MEMBERS)"""
        seconds = parse_duration(duration)
        if seconds > 2419200:
            toolong_embed = EmbedUtils.warning_embed(
                "❗ | The timeout duration must be less than 28 days!"
            )
            await ctx.send(embed=toolong_embed)

        await user.timeout(timedelta(seconds=seconds), reason=reason)
        timeout_embed = EmbedUtils.create_embed(
            title="Timed out user",
            description=f"🔇 | Timed out {user.mention} for {duration}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=timeout_embed)

    @commands.hybrid_command(name="unmute", aliases=["untimout"])
    @check_perms("moderate_members")
    async def moderator_unmute_or_untimeout(
        self,
        ctx: commands.Context,
        user: discord.Member,
    ):
        """Removes timeout/mute from a specified member (Requires MODERATE_MEMBERS)"""
        await user.timeout(None)
        timeout_embed = EmbedUtils.create_embed(
            title="Time out removed",
            description=f"🔇 | Removed timeout for {user.mention}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=timeout_embed)

    @commands.hybrid_command(name="createrole")
    @check_perms("manage_roles")
    async def moderator_create_role(self, ctx: commands.Context, *, role_name: str):
        """Creates a new role with the specified name (Requires MANAGE_ROLES)"""
        new_role = await ctx.guild.create_role(name=role_name)
        embed = EmbedUtils.success_embed(
            f"✅ | Role `{new_role.name}` created successfully."
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="deleterole")
    @check_perms("manage_roles")
    async def moderator_delete_role(self, ctx: commands.Context, role: discord.Role):
        """Deletes a specified role (Requires MANAGE_ROLES)"""
        await role.delete()
        embed = EmbedUtils.success_embed(
            f"✅ | Role `{role.name}` deleted successfully."
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="setup_jail")
    @check_perms("administrator")
    async def setup_jail(self, ctx: commands.Context):
        """Sets up a jail system: creates a 'Jail' category, 'jail' channel, and 'Jailed' role. Restricts jailed users to only see the jail channel."""
        guild = ctx.guild
        # Create 'Jailed' role if it doesn't exist
        jailed_role = discord.utils.get(guild.roles, name="Jailed")
        if not jailed_role:
            jailed_role = await guild.create_role(
                name="Jailed", reason="Jail system setup"
            )

        # Deny all permissions for @everyone in jail channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            jailed_role: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
        }

        # Create 'Jail' category if it doesn't exist
        category = discord.utils.get(guild.categories, name="Jail")
        if not category:
            category = await guild.create_category("Jail", reason="Jail system setup")

        # Create 'jail' channel if it doesn't exist
        jail_channel = discord.utils.get(category.channels, name="jail")
        if not jail_channel:
            jail_channel = await guild.create_text_channel(
                "jail",
                category=category,
                overwrites=overwrites,
                reason="Jail system setup",
            )

        # Set permissions for all other roles to not view the jail channel
        for role in guild.roles:
            if role not in [guild.default_role, jailed_role, guild.me.top_role]:
                await jail_channel.set_permissions(role, view_channel=False)

        # Set view_channel=False for 'Jailed' role on all channels except 'jail'
        for channel in guild.channels:
            if channel != jail_channel:
                try:
                    await channel.set_permissions(jailed_role, view_channel=False)
                except Exception:
                    pass

        embed = EmbedUtils.success_embed(
            "✅ | Jail system setup complete! 'Jailed' role, 'Jail' category, and 'jail' channel created. Jailed users can only see the jail channel."
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="jail")
    @check_perms("manage_members")
    async def jail_member(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: Optional[str] = "1d",
        *,
        reason: str = "No reason provided.",
    ):
        """Jails a member by assigning the 'Jailed' role and removing other roles for a duration."""
        guild = ctx.guild
        jailed_role = discord.utils.get(guild.roles, name="Jailed")
        if not jailed_role:
            err_embed = EmbedUtils.error_embed(
                "❗ | 'Jailed' role does not exist. Please run /setup_jail first."
            )
            await ctx.send(embed=err_embed)
            return

        seconds = self.parse_duration(duration)
        if seconds is None or seconds <= 0:
            err_embed = EmbedUtils.error_embed(
                "❗ | Invalid duration format. Use something like '12h' or '30d'."
            )
            await ctx.send(embed=err_embed)
            return

        # Remove all roles except @everyone and assign 'Jailed' role
        roles_to_remove = [
            role
            for role in member.roles
            if role != guild.default_role and role != jailed_role
        ]
        try:
            await member.remove_roles(*roles_to_remove, reason=f"Jailed: {reason}")
            await member.add_roles(jailed_role, reason=f"Jailed: {reason}")
        except discord.Forbidden:
            err_embed = EmbedUtils.error_embed(
                "❗ | I do not have permission to modify this member's roles. Try putting me higher in the role hierarchy."
            )
            await ctx.send(embed=err_embed)
            return

        embed = EmbedUtils.success_embed(
            f"🚨 | {member.mention} has been jailed for {duration}. Reason: {reason}"
        )
        await ctx.send(embed=embed)

        # Wait for the duration, then unjail
        await asyncio.sleep(seconds)
        try:
            await member.remove_roles(jailed_role, reason="Jail duration expired.")
            unjail_embed = EmbedUtils.success_embed(
                f"🔓 | {member.mention} has been released from jail after {duration}."
            )
            await ctx.send(embed=unjail_embed)
        except Exception:
            pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
