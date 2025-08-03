import discord
import random

# import psycopg

from discord.ext import commands

# from dotenv import load_dotenv
# from os import getenv
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils
from src.utils.database import DatabaseUtils

logger = setup_logger()
# load_dotenv()
# DB_NAME = getenv("DB_NAME")
# DB_USER = getenv("DB_USER")
# DB_PASSWORD = getenv("DB_PASSWORD")
# DB_HOST = getenv("DB_HOST")
# DB_PORT = getenv("DB_PORT")

# DB_PARAMS = {
#     "dbname": DB_NAME,
#     "user": DB_USER,
#     "password": DB_PASSWORD,
#     "host": DB_HOST,
#     "port": DB_PORT,
# }


# def get_db_connection():
#     return psycopg.connect(**DB_PARAMS)


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # DatabaseUtils takes care of this
    # @commands.Cog.listener()
    # async def on_ready(self):
    #     conn = get_db_connection()
    #     cursor = conn.cursor()

    #     cursor.execute(
    #         """
    #         CREATE TABLE IF NOT EXISTS counting_channels (
    #             channel_id BIGINT PRIMARY KEY,
    #             count INTEGER DEFAULT 1
    #         )
    #         """
    #     )
    #     conn.commit()
    #     cursor.close()
    #     conn.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # conn = get_db_connection()
        # cursor = conn.cursor()
        channel_id = message.channel.id

        result = DatabaseUtils.execute_query(
            "SELECT count FROM counting_channels WHERE channel_id = %s",
            (channel_id,),
            fetch="one",
        )
        # cursor.execute(
        #     "SELECT count FROM counting_channels WHERE channel_id = %s", (channel_id,)
        # )
        # result = cursor.fetchone()

        if result:
            current_count = result[0]
            try:
                user_number = int(message.content)

                if user_number == current_count:
                    new_count = current_count + 1
                    DatabaseUtils.execute_query(
                        "UPDATE counting_channels SET count = %s WHERE channel_id = %s",
                        (new_count, channel_id),
                    )
                    await message.add_reaction("✅")
                else:
                    wrong_number_em = EmbedUtils.create_embed(
                        title="Wrong Number!",
                        description=f"""
                        ❌ | Wrong Number! The last correct number was {current_count}. Resetting back to 1.
                        """,
                    )
                    await message.channel.send(embed=wrong_number_em)
                    DatabaseUtils.execute_query(
                        "UPDATE counting_channels SET count = 1 WHERE channel_id = %s",
                        (channel_id,),
                    )
            except ValueError:
                invalid_int_embed = EmbedUtils.warning_embed(
                    "❗ | Please enter a valid number!"
                )
                await message.channel.send(embed=invalid_int_embed)

    @commands.hybrid_command(
        name="diceroll",
        description="A die gets rolled and gives a result 1-6",
        aliases=["dice", "roll"],
    )
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def games_diceroll(self, ctx: commands.Context):
        """A die gets rolled and gives a result 1-6"""
        dice_roll = random.randint(1, 6)
        response_embed = EmbedUtils.create_embed(
            title="Dice Roll 🎲",
            description=f"You rolled a `{dice_roll}`",
            color=discord.Color.random(),
        )
        await ctx.send(embed=response_embed)

    @games_diceroll.error
    async def games_diceroll_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldown_embed = EmbedUtils.cooldown_embed(remaining_time=error.retry_after)
            await ctx.send(embed=cooldown_embed)

    @commands.hybrid_command(
        name="csetup", description="Setup for the Counting Channel"
    )
    async def games_setup_counting(self, ctx: commands.Context):
        """Setup for the Counting Channel"""
        try:
            guild = ctx.guild
            existing_channel = discord.utils.get(guild.channels, name="counting")

            if existing_channel:
                result = DatabaseUtils.execute_query(
                    "SELECT count FROM counting_channels WHERE channel_id = %s",
                    (existing_channel.id,),
                    fetch="one",
                )

                if result is None:
                    DatabaseUtils.execute_query(
                        "INSERT INTO counting_channels (channel_id, count) VALUES (%s, 1)",
                        (existing_channel.id,),
                    )
                embed = EmbedUtils.warning_embed(
                    description=f"A counting channel already exists! Channel: {existing_channel.mention}"
                )
                await ctx.send(embed=embed)
                return

            counting_channel = await guild.create_text_channel("counting")
            DatabaseUtils.execute_query(
                "INSERT INTO counting_channels (channel_id, count) VALUES (%s, 1)",
                (counting_channel.id,),
            )
            embed = EmbedUtils.success_embed(
                description=f"Counting channel created: {counting_channel.mention}",
            )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in games_setup_counting: {e}")
            await ctx.send(f"An error occurred: {e}")


async def setup(bot):
    await bot.add_cog(Games(bot))
