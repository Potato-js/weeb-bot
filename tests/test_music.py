import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import wavelink
from src.cogs.music import Music
from src.utils.errors import PlayerIsNotAvailable

# FILE: src/cogs/test_music.py


# Dummy QueueMode to simulate wavelink.QueueMode if needed
NORMAL = wavelink.QueueMode.normal
LOOP = wavelink.QueueMode.loop


@pytest.fixture()
def dummy_bot():
    return MagicMock()


@pytest.fixture()
def cog(dummy_bot):
    return Music(dummy_bot)


@pytest.fixture()
def mock_queue():
    queue = MagicMock()
    queue.shuffle = AsyncMock()
    # Set __len__ to return 5 songs, for example
    queue.__len__.return_value = 5
    # Simulate queue mode attribute
    queue.mode = NORMAL
    return queue


@pytest.fixture()
def mock_player(mock_queue):
    player = MagicMock()
    player.queue = mock_queue
    # For loop command test, allow toggling current track
    player.current = True
    # For pause/resume, simulate paused attribute
    player.paused = False
    # Simulate skip method
    player.skip = AsyncMock()
    # Simulate play, disconnect, and set_volume methods when needed
    player.play = AsyncMock()
    player.disconnect = AsyncMock()
    player.set_volume = AsyncMock()
    return player


@pytest.fixture()
def mock_ctx(mock_player):
    ctx = MagicMock()
    # voice_client is our fake player
    ctx.voice_client = mock_player
    ctx.send = AsyncMock()
    ctx.message = MagicMock()
    ctx.message.add_reaction = AsyncMock()
    # Also simulate guild attribute for commands like play
    ctx.guild = True
    # Provide an author with a voice channel for play command if needed
    ctx.author = MagicMock()
    ctx.author.voice = MagicMock()
    ctx.author.voice.channel = MagicMock()
    # For channel mention in already connected voice channel scenario
    ctx.channel = MagicMock()
    ctx.channel.mention = "#general"
    return ctx


@pytest.mark.asyncio
async def test_music_shuffle_queue_success(cog, mock_ctx, mock_player):
    dummy_embed = MagicMock()
    expected_description = "🔀 | Shuffling the queue of **5 songs**"
    with patch(
        "src.cogs.music.EmbedUtils.success_embed", return_value=dummy_embed
    ) as mock_success_embed:
        await cog.music_shuffle_queue.callback(cog, mock_ctx)
        # Assert that player's queue.shuffle was awaited once
        mock_player.queue.shuffle.assert_awaited_once()
        # Assert that EmbedUtils.success_embed was called with expected description and title "Shuffling..."
        mock_success_embed.assert_called_once_with(
            description=expected_description, title="Shuffling..."
        )
        # Assert that ctx.send was awaited with the dummy embed
        mock_ctx.send.assert_awaited_once_with(embed=dummy_embed)


@pytest.mark.asyncio
async def test_music_shuffle_queue_no_voice_client(cog):
    ctx = MagicMock()
    ctx.voice_client = None
    ctx.send = AsyncMock()
    with pytest.raises(PlayerIsNotAvailable):
        await cog.music_shuffle_queue.callback(ctx)


@pytest.mark.asyncio
async def test_music_loop_track_enable(cog, mock_ctx, mock_player):
    # Set player.current true and queue.mode to NORMAL and patch success_embed.
    mock_player.current = True
    mock_player.queue.mode = NORMAL
    dummy_embed = MagicMock()
    with patch(
        "src.cogs.music.EmbedUtils.success_embed", return_value=dummy_embed
    ) as mock_success_embed:
        await cog.music_loop_track(mock_ctx)
        # Expect mode toggled to LOOP
        assert mock_player.queue.mode == LOOP
        mock_success_embed.assert_called_once_with(description="🔂 | Loop mode enabled")
        mock_ctx.send.assert_awaited_once_with(embed=dummy_embed)


@pytest.mark.asyncio
async def test_music_loop_track_disable(cog, mock_ctx, mock_player):
    # Set current true and queue.mode to LOOP (simulate already looping)
    mock_player.current = True
    mock_player.queue.mode = LOOP
    dummy_embed = MagicMock()
    with patch(
        "src.cogs.music.EmbedUtils.success_embed", return_value=dummy_embed
    ) as mock_success_embed:
        await cog.music_loop_track(mock_ctx)
        # Expect mode toggled back to NORMAL
        assert mock_player.queue.mode == NORMAL
        mock_success_embed.assert_called_once_with(
            description="🔂 | Loop mode disabled"
        )
        mock_ctx.send.assert_awaited_once_with(embed=dummy_embed)


@pytest.mark.asyncio
async def test_music_loop_track_no_voice_client(cog):
    ctx = MagicMock()
    ctx.voice_client = None
    ctx.send = AsyncMock()
    with pytest.raises(PlayerIsNotAvailable):
        await cog.music_loop_track(ctx)


@pytest.mark.asyncio
async def test_music_skip_success(cog, mock_ctx, mock_player):
    await cog.music_skip(mock_ctx)
    # Assert that player.skip was awaited once
    mock_player.skip.assert_awaited_once()
    # Assert reaction added to message
    mock_ctx.message.add_reaction.assert_awaited_once_with("✅")


@pytest.mark.asyncio
async def test_music_skip_no_voice_client(cog):
    ctx = MagicMock()
    ctx.voice_client = None
    ctx.message = MagicMock()
    ctx.message.add_reaction = AsyncMock()
    with pytest.raises(PlayerIsNotAvailable):
        await cog.music_skip(ctx)
