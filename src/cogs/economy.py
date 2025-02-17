import discord


from typing import Optional
from dotenv import load_dotenv
from os import getenv

from discord.ext import commands
from src.utils.economy import EconomyUtils
from src.utils.embeds import EmbedUtils
from src.utils.logger import setup_logger

logging = setup_logger()
load_dotenv()
DB_NAME = getenv("DB_NAME")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="balance", aliases=["bal"])
    async def economy_balance(
        self, ctx: commands.Context, member: Optional[discord.Member] = None
    ):
        """Shows the balance of a specified user or author"""
        if not member:
            member = ctx.author

        try:
            wallet, bank, maxbank = EconomyUtils.get_balance(user_id=member.id)
            balance_embed = EmbedUtils.create_embed(
                description=None,
                title=f"{member.name}'s Wave Wealth:",
                color=discord.Color.green(),
            )
            balance_embed.add_field(
                name="Blåhaj Bucks",
                value=f"<:blahajCoin:1339437832346796132> `{wallet}`",
                inline=False,
            )
            balance_embed.add_field(
                name="Blåhaj Vault", value=f"💳 `{bank}/{maxbank}`", inline=False
            )
            await ctx.send(embed=balance_embed)
        except Exception as e:
            print(e)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
