from typing import Optional

import discord

from discord.ext import commands
from src.utils.database import DatabaseUtils
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils

logger = setup_logger()


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseUtils()

    async def create_balance(self, user: discord.Member):
        query = "INSERT INTO bank (user_id, wallet, bank, maxbank) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING"
        self.db.execute_query(query, (str(user.id), 0, 100, 25000))

    async def get_balance(self, user: discord.Member):
        query = "SELECT wallet, bank, maxbank FROM bank WHERE user_id = %s"
        data = self.db.execute_query(query, (str(user.id),), fetch="one")
        if data is None:
            await self.create_balance(user)
            return 0, 100, 25000
        wallet, bank, maxbank = data[0], data[1], data[2]
        return wallet, bank, maxbank

    async def update_wallet(self, user: discord.Member, amount: int):
        query = "SELECT wallet FROM bank WHERE user_id = %s"
        data = self.db.execute_query(query, (str(user.id),), fetch="one")
        if data is None:
            await self.create_balance(user)
            return 0
        self.db.execute_query(
            "UPDATE bank SET wallet = %s WHERE user_id = %s",
            (data[0] + amount, str(user.id)),
        )

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     await asyncio.sleep(3)
    #     await self.setup_database()

    @commands.hybrid_command(name="balance", aliases=["bal"])
    async def economy_balance(
        self, ctx: commands.Context, member: Optional[discord.Member] = None
    ):
        """Check your balance."""
        if member is None:
            member = ctx.author

        wallet, bank, maxbank = await self.get_balance(member)
        embed = EmbedUtils.create_embed(title=f"{member.name}'s Balance")
        embed.add_field(
            name="Wallet", value=f"{wallet} <:blahajCoin:1339437832346796132>"
        )
        embed.add_field(
            name="Bank", value=f"{bank}/{maxbank} <:blahajCoin:1339437832346796132>"
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
