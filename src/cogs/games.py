import discord
import random
import sqlite3

from discord.ext import commands
from src.utils.logger import setup_logger
from src.utils.embeds import EmbedUtils

logger = setup_logger()


class Games(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Connect to DB
        conn = sqlite3.connect("./src/databases/counting.db")
        cursor = conn.cursor()

        # Create table if doesn't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS counting_channels (
            channel_id INTEGER PRIMARY KEY,
            count INTEGER DEFAULT 1
        )
        """
        )
        conn.commit()
        cursor.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return  # Ignore bot messages

        conn = sqlite3.connect("./src/databases/counting.db")
        cursor = conn.cursor()
        channel_id = message.channel.id

        # Check if the channel is a counting channel
        cursor.execute(
            "SELECT count FROM counting_channels WHERE channel_id = ?", (channel_id,)
        )
        result = cursor.fetchone()

        if result:
            current_count = result[0]
            try:
                user_number = int(message.content)

                if user_number == current_count:
                    new_count = current_count + 1
                    cursor.execute(
                        "UPDATE counting_channels SET count = ? WHERE channel_id = ?",
                        (new_count, channel_id),
                    )
                    conn.commit()
                    await message.add_reaction("✅")
                else:
                    await message.channel.send(
                        f"Incorrect Number! The last correct number was {current_count}. Resetting back to 1."
                    )
                    cursor.execute(
                        "UPDATE counting_channels SET count = 1 WHERE channel_id = ?",
                        (channel_id,),
                    )
                    conn.commit()
            except ValueError:
                await message.channel.send("Please enter a valid number!")
        else:
            # Ignore messages in non-counting channels
            pass

        cursor.close()
        conn.close()

        # Ensure other commands still work
        # await self.bot.process_commands(message)

    @commands.hybrid_command(
        name="diceroll",
        description="A die gets rolled and gives a result 1-6",
        aliases=["dice", "roll"],
    )
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def games_diceroll(self, ctx):
        """ "A die gets rolled and gives a result 1-6"""
        dice_roll = random.randint(1, 6)
        response_embed = EmbedUtils.create_embed(
            title="Dice Roll 🎲",
            description=f"You rolled a `{dice_roll}`",
            color=discord.Color.random(),
        )

        await ctx.send(embed=response_embed)
        # try:
        #     await ctx.send(embed=response_embed)
        # except Exception as e:
        #     logger.error(e)

    @games_diceroll.error
    async def games_diceroll_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldown_embed = EmbedUtils.cooldown_embed(remaining_time=error.retry_after)
            await ctx.send(embed=cooldown_embed)

    @commands.hybrid_command(
        name="csetup", description="Setup for the Counting Channel"
    )
    async def games_setup_counting(self, ctx):
        """Setup for the Counting Channel"""
        try:
            guild = ctx.guild
            existing_channel = discord.utils.get(guild.channels, name="counting")
            conn = sqlite3.connect("./src/databases/counting.db")
            cursor = conn.cursor()

            if existing_channel:
                # Check if the existing channel is in the database
                cursor.execute(
                    "SELECT count FROM counting_channels WHERE channel_id = ?",
                    (existing_channel.id,),
                )
                result = cursor.fetchone()
                if result is None:
                    cursor.execute(
                        "INSERT INTO counting_channels (channel_id, count) VALUES (?, 1)",
                        (existing_channel.id,),
                    )
                    conn.commit()
                embed = EmbedUtils.warning_embed(
                    description=f"A counting channel already exists! Channel: {existing_channel.mention}"
                )
                await ctx.send(embed=embed)
                logger.warning("Existing channel found and reused.")
                cursor.close()
                conn.close()
                return

            # Create the counting channel
            counting_channel = await guild.create_text_channel("counting")
            cursor.execute(
                "INSERT INTO counting_channels (channel_id, count) VALUES (?, 1)",
                (counting_channel.id,),
            )
            conn.commit()
            embed = EmbedUtils.success_embed(
                description=f"Counting channel created: {counting_channel.mention}",
            )

            await ctx.send(embed=embed)
            logger.warning("New counting channel created.")
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error in games_setup_counting: {e}")
            await ctx.send(f"An error occurred: {e}")


async def setup(bot):
    await bot.add_cog(Games(bot))
