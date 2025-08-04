import discord

from discord.ext import commands

from src.utils.logger import setup_logger

# from typing import Required, Optional

logger = setup_logger()


class InviteButtons(discord.ui.View):
    def __init__(self, inv: str):
        super().__init__()
        self.inv = inv
        self.add_item(discord.ui.Button(label="Invite Link", url=self.inv))

    @discord.ui.button(label="Invite Btn", style=discord.ButtonStyle.blurple)
    async def inviteBtn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(self.inv, ephemeral=True)


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check the bot's latency")
    async def utilities_ping(self, ctx: commands.Context):
        """Check the bot's latency"""
        await ctx.send(f"Pong! {self.bot.latency}")

    @commands.hybrid_command(name="invite")
    async def utilities_invite(self, ctx: commands.Context):
        """Test Command for buttons"""
        inv = await ctx.channel.create_invite()
        await ctx.send("Click the button!", view=InviteButtons(str(inv)))


async def setup(bot):
    await bot.add_cog(Utils(bot))
