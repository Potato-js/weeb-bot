import unittest

from unittest.mock import MagicMock, AsyncMock, patch

from discord.ext import commands
from discord import Intents
from src.cogs.fakeperms import FakePerms
from src.utils.embeds import EmbedUtils


class TestFakePerms(
    unittest.IsolatedAsyncioTestCase
):  # TODO: finish this unit test up :L
    async def asyncSetUp(self):
        self.bot = commands.Bot(command_prefix="!", intents=Intents.all())
        self.fakeperms = FakePerms(self.bot)
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

        await self.bot.add_cog(self.fakeperms)

        self.ctx = MagicMock()
        self.ctx.author = MagicMock()
        self.ctx.author.guild_permissions = MagicMock()
        self.ctx.send = AsyncMock()

    @patch("src.utils.checks.check_perms")
    async def test_kick_with_decorator_allow(self, mock_check_perms):
        pass
