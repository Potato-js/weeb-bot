import unittest

from unittest.mock import MagicMock, patch
from discord.ext import commands
from discord import Intents
from src.utils.checks import check_perms


class TestCheckPerms(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = commands.Bot(command_prefix="!", intents=Intents.all())
        self.fakeperms = MagicMock()  # Mock the FakePerms cog
        self.fakeperms.permission_flags = {
            "KICK_MEMBERS": 1,
            "BAN_MEMBERS": 2,
            "ADMINISTRATOR": 4,
            "MANAGE_CHANNELS": 8,
            "MANAGE_GUILD": 16,
            "MANAGE_MESSAGES": 32,
            "MUTE_MEMBERS": 64,
            "DEFEAN_MEMBERS": 128,
            "CHANGE_NICKNAME": 256,
            "MANAGE_NICKNAMES": 512,
            "MANAGE_ROLES": 1024,
            "MODERATE_MEMBERS": 2048,
        }

        self.fakeperms.get_role_permissions = MagicMock()
        self.bot.get_cog = MagicMock(return_value=self.fakeperms)

        # Mock context
        self.ctx = MagicMock()
        self.ctx.bot = self.bot
        self.ctx.author = MagicMock()
        self.ctx.author.guild_permissions = MagicMock()
        self.ctx.author.roles = []

    async def run_check(self, perm_name: str):
        check = check_perms(perm_name)
        predicate = check.predicate
        return await predicate(self.ctx)

    @patch("discord.ext.commands.Context")
    async def test_admin_ban(self, mock_ctx):
        self.ctx.author.guild_permissions.administrator = True
        result = await self.run_check("ban_members")
        self.assertTrue(result)

    @patch("discord.ext.commands.Context")
    async def test_admin_kick(self, mock_ctx):
        self.ctx.author.guild_permissions.administrator = True
        result = await self.run_check("kick_members")
        self.assertTrue(result)

    @patch("discord.ext.commands.Context")
    async def test_kick_permission(self, mock_ctx):
        self.ctx.author.guild_permissions.administrator = False
        self.fakeperms.get_role_permissions.return_value = 1  # KICK_MEMBERS flag
        self.ctx.author.roles = [MagicMock(id=1)]
        result = await self.run_check("kick_members")
        self.assertTrue(result)

    @patch("discord.ext.commands.Context")
    async def test_kick_no_ban_permission(self, mock_ctx):
        self.ctx.author.guild_permissions.administrator = False
        self.fakeperms.get_role_permissions.return_value = 1  # KICK_MEMBERS flag
        self.ctx.author.roles = [MagicMock(id=1)]
        with self.assertRaises(commands.MissingPermissions):
            await self.run_check("ban_members")

    @patch("discord.ext.commands.Context")
    async def test_ban_permission(self, mock_ctx):
        self.ctx.author.guild_permissions.administrator = False
        self.fakeperms.get_role_permissions.return_value = 2  # BAN_MEMBERS flag
        self.ctx.author.roles = [MagicMock(id=1)]
        result = await self.run_check("ban_members")
        self.assertTrue(result)

    @patch("discord.ext.commands.Context")
    async def test_ban_no_kick_permission(self, mock_ctx):
        self.ctx.author.guild_permissions.administrator = False
        self.fakeperms.get_role_permissions.return_value = 2  # BAN_MEMBERS flag
        self.ctx.author.roles = [MagicMock(id=1)]
        with self.assertRaises(commands.MissingPermissions):
            await self.run_check("kick_members")

    @patch("discord.ext.commands.Context")
    async def test_no_permissions_ban(self, mock_ctx):
        self.ctx.author.guild_permissions.administrator = False
        self.fakeperms.get_role_permissions.return_value = 0  # No flags
        self.ctx.author.roles = [MagicMock(id=1)]
        with self.assertRaises(commands.MissingPermissions):
            await self.run_check("ban_members")

    @patch("discord.ext.commands.Context")
    async def test_no_permissions_kick(self, mock_ctx):
        self.ctx.author.guild_permissions.administrator = False
        self.fakeperms.get_role_permissions.return_value = 0  # No flags
        self.ctx.author.roles = [MagicMock(id=1)]
        with self.assertRaises(commands.MissingPermissions):
            await self.run_check("kick_members")


if __name__ == "__main__":
    unittest.main()
