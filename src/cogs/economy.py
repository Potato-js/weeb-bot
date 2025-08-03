import asyncio

from discord.ext import commands
from src.utils.database import DatabaseUtils


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseUtils()

    async def create_balance(self, user):
        query = "INSERT INTO bank VALUES (%s, %s, %s, %s)"
        self.db.execute_query(query, (user.id, 0, 100, 25000))

    async def get_balance(self, user):
        query = "SELECT wallet, bank, maxbank FROM bank WHERE user = %s"
        data = self.db.execute_query(query, (user.id,), fetch="one")
        if data is None:
            await self.create_balance(user)
            return 0, 100, 25000
        wallet, bank, maxbank = data[0], data[1], data[2]
        return wallet, bank, maxbank

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     await asyncio.sleep(3)
    #     await self.setup_database()


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
