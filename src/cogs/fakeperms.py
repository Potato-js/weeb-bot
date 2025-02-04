import discord
import json
import sqlite3

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from src.utils.checks import is_server_owner
from src.utils.errors import MissingParameter

logger = setup_logger()


class FakePerms(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = "./src/databases/fakeperms.db"
        self.permission_file = "./json/permissions.json"
        self.permission_flags = self.load_permission_flags()
        self._setup_database()

    def load_permission_flags(self):
        """
        Load permission flags from the JSON file.
        """
        try:
            with open(self.permission_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Permission file {self.permission_file} not found.")
            return {}

    def _setup_database(self):
        """
        Set up the SQLite database for storing role permissions.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS role_permissions (
                    role_id INTEGER PRIMARY KEY,
                    permissions INTEGER NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def get_role_permissions(self, role_id: int):
        """
        Retrieve the permissions for a role from the database.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            c.execute(
                """
                SELECT permissions FROM role_permissions WHERE role_id = ?
                """,
                (role_id,),
            )
            result = c.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()

    def set_role_permissions(self, role_id: int, permissions: int):
        """
        Save permissions for a role in the database.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO role_permissions (role_id, permissions) VALUES (?, ?)
                ON CONFLICT(role_id) DO UPDATE SET permissions = excluded.permissions
                """,
                (role_id, permissions),
            )
            conn.commit()
        finally:
            conn.close()

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, MissingParameter):  # TODO: Fix this not printing
            missing_param = error.parameter_name
            error_embed = EmbedUtils.error_embed(
                f"⛔ | Missing parameter: **{missing_param}**"
            )
            await ctx.send(embed=error_embed)

    @commands.hybrid_group(
        name="fakeperms",
        description="Manage Fake Permissions for roles.",
        aliases=["fp"],
    )
    @is_server_owner()
    async def mod_fakeperms(self, ctx):
        """
        Base command for the `fakeperms` hybrid group.
        """
        pass

    @mod_fakeperms.command(name="grant", help="Grant a permission to a role.")
    async def fp_grant_permission(self, ctx, role: discord.Role, perm_name: str):
        perm_flag = self.permission_flags.get(perm_name.upper())
        if not perm_flag:
            embed = EmbedUtils.error_embed(
                f"⛔ | Permission `{perm_name}` does not exist."
            )
            return await ctx.send(embed=embed)

        current_perms = self.get_role_permissions(role.id)
        new_perms = current_perms | perm_flag
        self.set_role_permissions(role.id, new_perms)

        embed = EmbedUtils.success_embed(
            f"✅ | Permission `{perm_name}` granted to role {role.mention}."
        )
        await ctx.send(embed=embed)

    @mod_fakeperms.command(name="revoke", help="Revoke a permission from a role.")
    async def fp_revoke_permission(self, ctx, role: discord.Role, *, perm_name: str):
        if role is None:
            raise MissingParameter(role)

        perm_flag = self.permission_flags.get(perm_name.upper())
        if not perm_flag:
            embed = EmbedUtils.error_embed(
                f"⛔ | Permission `{perm_name}` does not exist."
            )
            return await ctx.send(embed=embed)

        current_perms = self.get_role_permissions(role.id)
        new_perms = current_perms & ~perm_flag
        self.set_role_permissions(role.id, new_perms)

        embed = EmbedUtils.success_embed(
            f"✅ | Permission `{perm_name}` revoked from role {role.mention}."
        )
        await ctx.send(embed=embed)

    @mod_fakeperms.command(name="list", help="List permissions for a role.")
    async def fp_list_permissions(self, ctx, role: discord.Role):
        current_perms = self.get_role_permissions(role.id)
        perms_list = [
            name for name, flag in self.permission_flags.items() if current_perms & flag
        ]

        if perms_list:
            embed = EmbedUtils.create_embed(
                title=f"Permissions for {role.name}",
                description="\n".join(perms_list),
                color=discord.Color.blue(),
            )
        else:
            embed = EmbedUtils.error_embed(
                f"⛔ | Role `{role.name}` has no permissions."
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(FakePerms(bot))
