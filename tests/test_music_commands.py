import sys
import types
import asyncio
from unittest.mock import AsyncMock
import pytest

from src.cogs.music import Music
from src.utils.embeds import EmbedUtils

# Stub discord.ext.commands so the cog can be imported without the real library
commands_stub = types.SimpleNamespace()


class DummyCog:
    @staticmethod
    def listener(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


commands_stub.Cog = DummyCog
commands_stub.Bot = object
commands_stub.Context = object
commands_stub.CommandError = Exception


def hybrid_command(*args, **kwargs):
    def decorator(func):
        return func

    return decorator


commands_stub.hybrid_command = hybrid_command


class DummyColor:
    @staticmethod
    def random():
        return DummyColor()

    @staticmethod
    def green():
        return DummyColor()

    @staticmethod
    def red():
        return DummyColor()

    @staticmethod
    def yellow():
        return DummyColor()


class DummyEmbed:
    def __init__(self, *args, **kwargs):
        pass

    def set_footer(self, *args, **kwargs):
        pass

    def set_thumbnail(self, *args, **kwargs):
        pass

    def set_image(self, *args, **kwargs):
        pass

    def add_field(self, *args, **kwargs):
        pass

    def set_author(self, *args, **kwargs):
        pass


discord_stub = types.SimpleNamespace(
    ext=types.SimpleNamespace(commands=commands_stub),
    ClientException=Exception,
    Color=DummyColor,
    Embed=DummyEmbed,
)

sys.modules.setdefault("discord", discord_stub)
sys.modules.setdefault("discord.ext", types.SimpleNamespace(commands=commands_stub))

# Provide a stub for python-dotenv
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

# Stub minimal wavelink API used by the music cog
wavelink_stub = types.SimpleNamespace()


class DummyPlayer:
    def __init__(self):
        self.skip = AsyncMock()
        self.disconnect = AsyncMock()


wavelink_stub.Player = DummyPlayer
wavelink_stub.QueueMode = types.SimpleNamespace(normal=1, loop=2)
wavelink_stub.NodeReadyEventPayload = object
wavelink_stub.TrackStartEventPayload = object
wavelink_stub.TrackEndEventPayload = object
wavelink_stub.Playable = types.SimpleNamespace(
    search=lambda *a, **k: [], recommended=False
)
wavelink_stub.Playlist = object
wavelink_stub.Search = list
wavelink_stub.Node = object
wavelink_stub.Pool = types.SimpleNamespace(connect=AsyncMock())

sys.modules.setdefault("wavelink", wavelink_stub)


class DummyMessage:
    def __init__(self):
        self.add_reaction = AsyncMock()


class DummyContext:
    def __init__(self, player):
        self.voice_client = player
        self.message = DummyMessage()
        self.send = AsyncMock()


def test_music_skip_skips_track():
    """Ensure the skip command skips the current track."""
    bot = types.SimpleNamespace()
    music_cog = Music(bot)
    player = DummyPlayer()
    ctx = DummyContext(player)

    asyncio.run(music_cog.music_skip(ctx))

    player.skip.assert_awaited_once_with()
    ctx.message.add_reaction.assert_awaited_once_with("✅")


def test_music_disconnect_disconnects_and_sends_message(
    monkeypatch: pytest.MonkeyPatch,
):
    """Ensure the disconnect command disconnects the player and notifies the user."""
    bot = types.SimpleNamespace()
    music_cog = Music(bot)
    player = DummyPlayer()
    ctx = DummyContext(player)

    monkeypatch.setattr(EmbedUtils, "success_embed", lambda *a, **k: "embed")
    asyncio.run(music_cog.music_disconnect(ctx))

    player.disconnect.assert_awaited_once_with()
    ctx.send.assert_awaited_once_with(embed="embed")
