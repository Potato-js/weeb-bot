import discord
import json

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from src.utils.checks import is_server_owner
from src.utils.database import DatabaseUtils

logger = setup_logger()


class FakePerms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseUtils()
        self.permission_file = "./src/json/permissions.json"
        self.permission_flags = self.load_permission_flags()

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

    def get_role_permissions(self, role_id: int):
        """
        Retrieve the permissions for a role from the database.
        """
        try:
            result = self.db.execute_query(
                "SELECT permissions FROM role_permissions WHERE role_id = %s",
                (role_id,),
                fetch="one",
            )
            return result[0] if result else 0
        except Exception as e:
            logger.error(
                f"Error retrieving role permissions for role_id {role_id}: {e}"
            )
            return 0

    def set_role_permissions(self, role_id: int, permissions: int):
        """
        Set the permissions for a role in the database.
        """
        try:
            self.db.execute_query(
                """
                INSERT INTO role_permissions (role_id, permissions) VALUES (%s, %s)
                ON CONFLICT (role_id) DO UPDATE SET permissions = EXCLUDED.permissions
                """,
                (role_id, permissions),
            )
        except Exception as e:
            logger.error(f"Error setting role permissions for role_id {role_id}: {e}")

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


async def setup(bot: commands.Bot):
    await bot.add_cog(FakePerms(bot))
