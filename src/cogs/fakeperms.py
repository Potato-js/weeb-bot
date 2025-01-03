import discord
import json
import sqlite3

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from src.utils.checks import is__server_owner


class FakePerms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "./src/databases/fakeperms.db"
        self.permission_file = "./json/permissions.json"
        self.permission_flags = self.load_permission_flags()
        self._setup_database()

    def load_permission_flags(self):
        with open(self.permission_file, "r") as f:
            return json.load(f)

    def _setup_database(self):
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
        conn.close()

    def get_role_permissions(self, role_id: int):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            SELECT permissions FROM role_permissions WHERE role_id = ?
            """,
            (role_id,),
        )
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0

    def set_role_permissions(self, role_id: int, permissions: int):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO role_permissions (role_id, permissions) VALUES (?, ?)
            ON CONFLICT(role_id) DO UPDATE SET permissions = excluded.permissions
            """,
            (role_id, permissions),
        )
        conn.commit()
        conn.close()

    @commands.hybrid_group(
        name="fakeperms", description="Fake Permissions Command Group", aliases=["fp"]
    )
    @is__server_owner()
    async def mod_fakeperms(self):
        pass

    @mod_fakeperms.command(name="grant", help="Grant permissions to a role.")
    async def fp_grant_permission(self, ctx, role: discord.Role, perm_name: str):
        perm_flag = self.permission_flags.get(perm_name.upper())
        if not perm_flag:
            embed = EmbedUtils.error_embed(f"Permission `{perm_name}` does not exist.")
            return await ctx.send(embed=embed)

        current_perms = self.get_role_permissions(role.id)
        new_perms = current_perms | perm_flag
        self.set_role_permissions(role.id, new_perms)

        embed = EmbedUtils.success_embed(
            f"Permission `{perm_name}` granted to role {role.mention}."
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(FakePerms(bot))
