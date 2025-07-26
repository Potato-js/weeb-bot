import sys
import types
import asyncio
from unittest.mock import AsyncMock
import pytest

# Provide a minimal stub of discord.ext.commands so the cog can be imported
commands_stub = types.SimpleNamespace()
commands_stub.Cog = object
commands_stub.Bot = object
commands_stub.Context = object

def hybrid_command(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

commands_stub.hybrid_command = hybrid_command

sys.modules.setdefault("discord", types.SimpleNamespace(ext=types.SimpleNamespace(commands=commands_stub)))
sys.modules.setdefault("discord.ext", types.SimpleNamespace(commands=commands_stub))

from src.cogs.utils import Utils


class DummyContext:
    def __init__(self):
        self.send = AsyncMock()


def test_ping_command_sends_latency():
    """Ensure the ping command sends the bot latency."""
    bot = types.SimpleNamespace(latency=123)
    utils_cog = Utils(bot)
    ctx = DummyContext()

    asyncio.run(utils_cog.utilities_ping(ctx))

    ctx.send.assert_awaited_once_with(f"Pong! {bot.latency}")
