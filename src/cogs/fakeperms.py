from discord.ext import commands

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils


class FakePerms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="fakeperms", description="Fake Permissions Command Group", aliases=["fp"]
    )
    async def mod_fakeperms(self):
        pass


async def setup(bot):
    await bot.add_cog(FakePerms(bot))
