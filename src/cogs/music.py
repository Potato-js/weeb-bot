import asyncio

from typing import cast

import discord
import wavelink

from discord.ext import commands

from dotenv import load_dotenv
from os import getenv
from src.utils.embeds import EmbedUtils
from src.utils.logger import setup_logger
from src.utils.errors import PlayerIsNotAvailable


logger = setup_logger()


class MusicPanel(discord.ui.View):  # TODO: Complete Music Panel
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="loop", style=discord.ButtonStyle.grey)
    async def panel_loop(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        player: wavelink.Player = cast(
            wavelink.Player, interaction.client.voice_clients
        )
        if player.current:
            if player.queue.mode == wavelink.QueueMode.normal:
                player.queue.mode = wavelink.QueueMode.loop
                loop_embed = EmbedUtils.success_embed(
                    description="🔂 | Loop mode enabled"
                )
                await interaction.response.send_message(
                    embed=loop_embed, ephemeral=True
                )
            else:
                player.queue.mode = wavelink.QueueMode.normal
                loop_embed = EmbedUtils.success_embed(
                    description="🔂 | Loop mode disabled"
                )
                await interaction.response.send_message(
                    embed=loop_embed, ephemeral=True
                )


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def setup_hook(self) -> None:
        load_dotenv()
        LAVALINK_URI = getenv("LAVALINK_URL")
        LAVALINK_PASS = getenv("LAVALINK_PASSWORD")
        nodes = [
            wavelink.Node(uri=LAVALINK_URI, password=LAVALINK_PASS),
        ]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=None)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.setup_hook()

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, PlayerIsNotAvailable):
            err_embed = EmbedUtils.error_embed(error)
            await ctx.send(embed=err_embed)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(
        self, payload: wavelink.NodeReadyEventPayload
    ) -> None:
        logger.info(
            f"Wavelink Node connected: {payload.node} | Resumed: {payload.resumed}"
        )

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self, payload: wavelink.TrackStartEventPayload
    ) -> None:
        player: wavelink.Player = payload.player
        if not player:
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        np_embed = EmbedUtils.create_embed(
            title="Now Playing",
            description=f"🔊 | [**{track.title}** by `{track.author}`]({track.uri})",
        )

        if track.artwork:
            np_embed.set_image(url=track.artwork)

        if original and original.recommended:
            np_embed.description += (
                f"\n\n`This track was recommended via {track.source}`"
            )

        if track.album.name:
            np_embed.add_field(name="Album", value=track.album.name)

        await player.home.send(embed=np_embed)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player: wavelink.Player = payload.player
        if not player:
            return

        if player.queue.mode == wavelink.QueueMode.loop:
            await player.play(payload.track)

        if not player.queue.is_empty:
            new = await player.queue.get_wait()
            await player.play(new)
        else:
            await asyncio.sleep(120)
            await player.stop()
            await player.disconnect()

    @commands.hybrid_command(name="play", aliases=["p"])
    async def music_play(self, ctx: commands.Context, *, query: str):
        """Plays a song from a playlist/link/query"""
        if not ctx.guild:
            return

        player: wavelink.Player
        player = cast(wavelink.Player, ctx.voice_client)

        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            except AttributeError:
                joinvc_embed = EmbedUtils.error_embed(
                    title="Unable to join",
                    description="⚠ | Join a voice channel before running this command!",
                )
                await ctx.send(embed=joinvc_embed)
                return
            except discord.ClientException:
                error_embed = EmbedUtils.error_embed(
                    description="⛔ | I was unable to join the VC. Try again!"
                )
                await ctx.send(embed=error_embed)
                return

        if not hasattr(player, "home"):
            player.home = ctx.channel
        elif player.home != ctx.channel:
            description = f"❗ | You can only play songs in {player.home.mention}, as the player strated there."
            alreadyvc_embed = EmbedUtils.warning_embed(description=description)
            await ctx.send(embed=alreadyvc_embed)
            return

        tracks: wavelink.Search = await wavelink.Playable.search(query)
        if not tracks:
            notrack_embed = EmbedUtils.warning_embed(
                title="No tracks found",
                description=f"⚠ | {ctx.author.mention} - Could not find any tracks with the query. Is the playlist/video private?",
            )
            await ctx.send(embed=notrack_embed)
            return

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)
            playlistadded_embed = EmbedUtils.success_embed(
                description=f"✅ | Added the playlist [**`{tracks.name}`**]({tracks.url}) ({added} songs) to the queue!"
            )
            await ctx.send(embed=playlistadded_embed)
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            trackadded_embed = EmbedUtils.success_embed(
                description=f"✅ | Added [**`{track}`**]({track.uri}) to the queue!"
            )
            await ctx.send(embed=trackadded_embed)

        if not player.playing:
            await player.play(player.queue.get(), volume=30)

    @commands.hybrid_command(name="skip")
    async def music_skip(self, ctx: commands.Context):
        """ "Skips the current song"""
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerIsNotAvailable()

        await player.skip()
        await ctx.message.add_reaction("✅")

    @commands.hybrid_command(name="toggle", aliases=["pause", "resume", "r"])
    async def music_play_pause(self, ctx: commands.Context):
        """Pause or Resume the player depending on its state"""
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerIsNotAvailable()

        await player.pause(not player.paused)
        await ctx.message.add_reaction("✅")

    @commands.hybrid_command(name="volume", aliases=["vol", "v"])
    async def music_volume(self, ctx: commands.Context, value: int):
        """Sets the volume of the player between 0-100"""
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerIsNotAvailable()

        if value > 100:
            tooloud_em = EmbedUtils.warning_embed(
                description="⚠ | Woah there that's too loud! Make sure it's a value between `0-100`!",
                title="Don't go deaf now!",
            )
            await ctx.send(embed=tooloud_em)
        elif value < 0:
            tooquiet_em = EmbedUtils.warning_embed(
                description="⚠ | We can't even hear it! Make sure it's a value between `0-100`",
                title="I CAN'T HEAR YOU!",
            )
            await ctx.send(embed=tooquiet_em)
        else:
            await player.set_volume(value)
            await ctx.message.add_reaction("✅")

    @commands.hybrid_command(name="disconnect", aliases=["stop", "dc", "leave"])
    async def music_disconnect(self, ctx: commands.Context):
        """Disconnects the player from the channel"""
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerIsNotAvailable()

        await player.disconnect()
        dc_embed = EmbedUtils.success_embed("👋 | See you next time!")
        await ctx.send(embed=dc_embed)

    @commands.hybrid_command(name="loop", aliases=["repeat", "l"])
    async def music_loop_track(self, ctx: commands.Context):
        """Loops the current track"""
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerIsNotAvailable()

        if player.current:
            if player.queue.mode == wavelink.QueueMode.normal:
                player.queue.mode = wavelink.QueueMode.loop
                loop_embed = EmbedUtils.success_embed(
                    description="🔂 | Loop mode enabled"
                )
                await ctx.send(embed=loop_embed)
            else:
                player.queue.mode = wavelink.QueueMode.normal
                loop_embed = EmbedUtils.success_embed(
                    description="🔂 | Loop mode disabled"
                )
                await ctx.send(embed=loop_embed)

    @commands.hybrid_command(name="shuffle", aliases=["sh"])
    async def music_shuffle_queue(self, ctx: commands.Context):
        """Shuffles the current track"""
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerIsNotAvailable()

        await player.queue.shuffle()
        shuffle_embed = EmbedUtils.success_embed(
            description=f"🔀 | Shuffling the queue of **{len(player.queue)} songs**",
            title="Shuffling...",
        )
        await ctx.send(embed=shuffle_embed)

    @commands.hybrid_command(name="panel")
    async def music_panel(self, ctx: commands.Context):
        # player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        # if not player:
        #     raise PlayerIsNotAvailable()

        await ctx.send(view=MusicPanel())


async def setup(bot):
    await bot.add_cog(Music(bot))
