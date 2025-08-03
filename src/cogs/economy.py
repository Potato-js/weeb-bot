import asyncio
import psycopg

from discord.ext import commands


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.db = psycopg.connect(DB_CONN)

    async def create_balance(user):
        conn = await psycopg.connect(DB_CONN)
        cursor = await conn.cursor()
        await cursor.execute(
            "INSERT INTO bank (user_id, wallet, bank, maxbank) VALUES (%s, %s, %s, %s)",
            (user.id, 0, 0, 1000000),
        )
        await conn.commit()
        await cursor.close()
        await conn.close()

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(3)
        await self.setup_database()


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
