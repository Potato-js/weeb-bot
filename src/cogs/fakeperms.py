import discord
import json
import psycopg

# from psycopg import sql
# from psycopg.extras import DictCursor

from discord.ext import commands
from dotenv import load_dotenv
from os import getenv
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from src.utils.checks import is_server_owner

logger = setup_logger()
load_dotenv()
DB_NAME = getenv("DB_NAME")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")


class FakePerms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_config = {
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "host": DB_HOST,
            "port": DB_PORT,
        }
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
        Set up the PostgreSQL database for storing role permissions.
        """
        try:
            conn = psycopg.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS role_permissions (
                    role_id BIGINT PRIMARY KEY,
                    permissions INTEGER NOT NULL
                )
                """
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Database setup error: {e}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def get_role_permissions(self, role_id: int):
        """
        Retrieve the permissions for a role from the database.
        """
        conn = None
        try:
            conn = psycopg.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT permissions FROM role_permissions WHERE role_id = %s
                """,
                (role_id,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(
                f"Error retrieving role permissions for role_id {role_id}: {e}"
            )
            return 0
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def set_role_permissions(self, role_id: int, permissions: int):
        """
        Set the permissions for a role in the database.
        """
        try:
            conn = psycopg.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO role_permissions (role_id, permissions) VALUES (%s, %s)
                ON CONFLICT (role_id) DO UPDATE SET permissions = EXCLUDED.permissions
                """,
                (role_id, permissions),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error setting role permissions for role_id {role_id}: {e}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.MissingRequiredArgument):
            param = error.param
            await ctx.send(
                embed=EmbedUtils.error_embed(
                    f"⛔ | Missing required parameter: `{param.name}`"
                )
            )

    @commands.hybrid_group(
        name="fakeperms",
        description="Manage Fake Permissions for roles.",
        aliases=["fp"],
    )
    @is_server_owner()
    async def mod_fakeperms(self, ctx: commands.Context):
        """
        Base command for the `fakeperms` hybrid group.
        """
        pass

    @mod_fakeperms.command(name="grant", help="Grant a permission to a role.")
    async def fp_grant_permission(
        self, ctx: commands.Context, role: discord.Role, perm_name: str
    ):
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
    async def fp_revoke_permission(
        self, ctx: commands.Context, role: discord.Role, *, perm_name: str
    ):
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
    async def fp_list_permissions(self, ctx: commands.Context, role: discord.Role):
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
