import random
import json

from typing import Optional

import discord

from discord.ext import commands
from src.utils.database import DatabaseUtils
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from src.utils.errors import AccountNotFound, InvalidFunds

logger = setup_logger()


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseUtils()
        self.cooldowns = {}
        self.economy_config = self.load_economy_config()

    def load_economy_config(self):
        """Load economy configuration from JSON file."""
        try:
            with open("./src/json/economy.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Economy config file not found.")
            return {}

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

    async def update_bank(self, user: discord.Member, amount: int):
        query = "SELECT wallet, bank, maxbank FROM bank WHERE user_id = %s"
        data = self.db.execute_query(query, (str(user.id),), fetch="one")
        if data is None:
            await self.create_balance(user)
            return 0
        capacity = int(data[2] - data[1])
        if amount > capacity:
            await self.update_wallet(user, amount)
            return 1
        self.db.execute_query(
            "UPDATE bank SET bank = %s WHERE user_id = %s",
            (data[1] + amount, str(user.id)),
        )

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     await asyncio.sleep(3)
    #     await self.setup_database()

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, AccountNotFound):
            err_embed = EmbedUtils.warning_embed(error)
            await ctx.send(embed=err_embed)
        elif isinstance(error, commands.CommandOnCooldown):
            embed = EmbedUtils.cooldown_embed(remaining_time=int(error.retry_after))
            await ctx.send(embed=embed)
        elif isinstance(error, InvalidFunds):
            err_embed = EmbedUtils.warning_embed(error)
            await ctx.send(embed=err_embed)

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
            name="Wallet 💳", value=f"{wallet} <:blahajCoin:1339437832346796132>"
        )
        embed.add_field(
            name="Bank 🏛️", value=f"{bank}/{maxbank} <:blahajCoin:1339437832346796132>"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="beg")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def economy_beg(self, ctx: commands.Context):
        """Beg for some money. Maybe you'll get lucky!"""
        # Get beg configuration
        beg_config = self.economy_config.get("beg", {})
        celebs = self.economy_config.get("celebs", {})
        success_messages = self.economy_config.get("beg_success", {})
        fail_messages = self.economy_config.get("beg_failed", {})

        min_amount = beg_config.get("min_amount", 1)
        max_amount = beg_config.get("max_amount", 100)
        success_rate = beg_config.get("success_rate", 0.7)

        # Random selection from celebs
        celeb_key = random.choice(list(celebs.keys()))
        chosen_name = celebs[celeb_key]

        # Proper weighted randomizer
        success_weight = int(success_rate * 100)  # Convert to percentage
        fail_weight = 100 - success_weight

        outcomes = ["success"] * success_weight + ["fail"] * fail_weight
        result = random.choice(outcomes)

        if result == "success":
            # Calculate amount with weighted distribution (lower amounts more common)
            weights = [
                40,
                30,
                20,
                10,
            ]  # 40% chance low, 30% med-low, 20% med-high, 10% high
            ranges = [
                (min_amount, min_amount + (max_amount - min_amount) // 4),
                (
                    min_amount + (max_amount - min_amount) // 4,
                    min_amount + (max_amount - min_amount) // 2,
                ),
                (
                    min_amount + (max_amount - min_amount) // 2,
                    min_amount + 3 * (max_amount - min_amount) // 4,
                ),
                (min_amount + 3 * (max_amount - min_amount) // 4, max_amount),
            ]

            chosen_range = random.choices(ranges, weights=weights)[0]
            amount = random.randint(chosen_range[0], chosen_range[1])

            res = await self.update_wallet(ctx.author, amount)
            if res == 0:
                raise AccountNotFound()

            success_key = random.choice(list(success_messages.keys()))
            message = success_messages[success_key].format(
                money=f"{amount} <:blahajCoin:1339437832346796132>"
            )

            embed = EmbedUtils.success_embed(f"🤲 | **{chosen_name}**: {message}")
        else:
            fail_key = random.choice(list(fail_messages.keys()))
            message = fail_messages[fail_key]

            embed = EmbedUtils.error_embed(f"😔 | **{chosen_name}**: {message}")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="withdraw")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def withdraw(self, ctx: commands.Context, amount):
        """Withdraw money from your bank."""
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        try:
            amount = int(amount)
        except ValueError:
            return await ctx.send(
                embed=EmbedUtils.error_embed(
                    "⛔ | Invalid amount. Please enter a valid number."
                )
            )

        if isinstance(amount, str):
            if amount.lower() == "all" or amount.lower() == "max":
                amount = int(wallet)
        else:
            amount = int(amount)

        bank_res = await self.update_bank(ctx.author, -amount)
        wallet_res = await self.update_wallet(ctx.author, amount)
        if bank_res == 0 or wallet_res == 0:
            raise AccountNotFound()
        elif bank_res == 1:
            raise InvalidFunds()

        wallet, bank, maxbank = await self.get_balance(ctx.author)
        embed = EmbedUtils.create_embed(title=f"{amount} has been withdrew!")
        embed.add_field(
            name="Updated Wallet 💳",
            value=f"{wallet} <:blahajCoin:1339437832346796132>",
        )
        embed.add_field(
            name="Updated Bank 🏛️",
            value=f"{bank}/{maxbank} <:blahajCoin:1339437832346796132>",
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="deposit", aliases=["dep"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def deposit(self, ctx: commands.Context, amount):
        """Deposit money into your bank."""
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        try:
            amount = int(amount)
        except ValueError:
            return await ctx.send(
                embed=EmbedUtils.error_embed(
                    "⛔ | Invalid amount. Please enter a valid number."
                )
            )

        if isinstance(amount, str):
            if amount.lower() == "all" or amount.lower() == "max":
                amount = int(bank)
        else:
            amount = int(amount)

        bank_res = await self.update_bank(ctx.author, -amount)
        wallet_res = await self.update_wallet(ctx.author, amount)
        if bank_res == 0 or wallet_res == 0:
            raise AccountNotFound()
        elif bank_res == 1:
            raise InvalidFunds()

        wallet, bank, maxbank = await self.get_balance(ctx.author)
        embed = EmbedUtils.create_embed(title=f"{amount} has been withdrew!")
        embed.add_field(
            name="Updated Wallet 💳",
            value=f"{wallet} <:blahajCoin:1339437832346796132>",
        )
        embed.add_field(
            name="Updated Bank 🏛️",
            value=f"{bank}/{maxbank} <:blahajCoin:1339437832346796132>",
        )
        await ctx.send(embed=embed)

    # @economy_beg.error
    # async def economy_beg_error(self, ctx: commands.Context, error):
    #     if isinstance(error, commands.CommandOnCooldown):
    #         embed = EmbedUtils.cooldown_embed(remaining_time=int(error.retry_after))
    #         await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
