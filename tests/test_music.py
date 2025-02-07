import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from discord.ext import commands
import wavelink
from src.cogs.music import Music
from src.utils.errors import PlayerIsNotAvailable


class TestMusicCog:
    @pytest.fixture(scope="class")
    def mock_voice_client(self):
        # Use AsyncMock for the entire voice client.
        voice_client = AsyncMock(spec=wavelink.Player)
        voice_client.connected = True
        voice_client.playing = False
        voice_client.paused = False

        # Ensure async methods are AsyncMock.
        voice_client.skip = AsyncMock()
        voice_client.pause = AsyncMock()
        voice_client.play = AsyncMock()
        voice_client.set_volume = AsyncMock()
        voice_client.disconnect = AsyncMock()

        # Set up the queue using AsyncMock for async methods.
        voice_client.queue = MagicMock()
        voice_client.queue.mode = wavelink.QueueMode.normal
        voice_client.queue.is_empty = False
        voice_client.queue.count = 5
        voice_client.queue.put_wait = AsyncMock()
        voice_client.queue.shuffle = AsyncMock()

        return voice_client

    @pytest.fixture(scope="class")
    def mock_bot(self):
        return MagicMock(spec=commands.Bot)

    @pytest.fixture(scope="class")
    def cog(self, mock_bot, mock_voice_client):
        cog = Music(mock_bot)
        cog.bot = mock_bot
        return cog

    @pytest.fixture
    def mock_ctx(self, mock_voice_client):
        ctx = MagicMock()
        # Simulate that the command author is in a voice channel.
        ctx.author.voice.channel = MagicMock()
        ctx.voice_client = mock_voice_client
        # Make ctx.send awaitable
        ctx.send = AsyncMock()
        # Set up the message attribute so that add_reaction is awaitable
        ctx.message = MagicMock()
        ctx.message.add_reaction = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_setup_hook(self, cog, mock_voice_client):
        with patch.object(
            wavelink.Pool, "connect", new_callable=AsyncMock
        ) as mock_connect:
            await cog.setup_hook()
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_play_command(self, cog, mock_ctx, mock_voice_client):
        # Create a fake track.
        mock_track = MagicMock()
        mock_track.uri = "test_uri"
        mock_track.title = "Test Track"

        with patch.object(
            wavelink.Playable,
            "search",
            new_callable=AsyncMock,
            return_value=[mock_track],
        ) as mock_search:
            await cog.music_play.callback(cog, mock_ctx, query="test query")
            mock_search.assert_called_once_with("test query")
            mock_voice_client.queue.put_wait.assert_called_once()
            mock_voice_client.play.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_command(self, cog, mock_ctx, mock_voice_client):
        await cog.music_skip.callback(cog, mock_ctx)
        mock_voice_client.skip.assert_called_once()

    @pytest.mark.asyncio
    async def test_toggle_command(self, cog, mock_ctx, mock_voice_client):
        initial_state = mock_voice_client.paused
        await cog.music_play_pause.callback(cog, mock_ctx)
        mock_voice_client.pause.assert_called_once_with(not initial_state)

    @pytest.mark.asyncio
    async def test_volume_command(self, cog, mock_ctx, mock_voice_client):
        await cog.music_volume.callback(cog, mock_ctx, 50)
        mock_voice_client.set_volume.assert_called_once_with(50)

    @pytest.mark.asyncio
    async def test_disconnect_command(self, cog, mock_ctx, mock_voice_client):
        await cog.music_disconnect.callback(cog, mock_ctx)
        mock_voice_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_loop_command(self, cog, mock_ctx, mock_voice_client):
        await cog.music_loop_track.callback(cog, mock_ctx)
        assert mock_voice_client.queue.mode == wavelink.QueueMode.loop
        await cog.music_loop_track.callback(cog, mock_ctx)
        assert mock_voice_client.queue.mode == wavelink.QueueMode.normal

    @pytest.mark.asyncio
    async def test_shuffle_command(self, cog, mock_ctx, mock_voice_client):
        await cog.music_shuffle_queue.callback(cog, mock_ctx)
        mock_voice_client.queue.shuffle.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, cog):
        mock_ctx = MagicMock()
        mock_ctx.voice_client = None
        mock_ctx.send = AsyncMock()
        with pytest.raises(PlayerIsNotAvailable):
            await cog.music_skip.callback(cog, mock_ctx)
