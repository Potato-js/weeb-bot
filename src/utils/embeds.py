import discord
from typing import Optional, List


class EmbedUtils:
    @staticmethod
    def create_embed(
        description: str,
        title: Optional[str] = None,
        color: discord.Color = discord.Color.blue(),
        fields: Optional[List[dict]] = None,
        footer: Optional[str] = "© 2025 weeaboo",
        thumbnail_url: Optional[str] = None,
        image_url: Optional[str] = None,
        author: Optional[dict] = None,
    ) -> discord.Embed:
        """
        Creates a Discord embed with the given parameters.

        :param description: The description of the embed (required).
        :param title: The title of the embed (optional).
        :param color: The color of the embed border (default: blue).
        :param fields: A list of dictionaries for embed fields. Each dictionary should have 'name', 'value', and optionally 'inline'.
        :param footer: Footer text for the embed (default: © 2024 weeaboo).
        :param thumbnail_url: URL for the thumbnail image (optional).
        :param image_url: URL for the main embed image (optional).
        :param author: A dictionary with 'name', 'url', and 'icon_url' for the author (optional).
        :return: A discord.Embed object.
        """
        embed = discord.Embed(title=title, description=description, color=color)

        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get("name", "No Name"),
                    value=field.get("value", "No Value"),
                    inline=field.get("inline", True),
                )

        if footer:
            embed.set_footer(text=footer)

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        if image_url:
            embed.set_image(url=image_url)

        if author:
            embed.set_author(
                name=author.get("name", ""),
                url=author.get("url", None),
                icon_url=author.get("icon_url", None),
            )

        return embed

    @staticmethod
    def success_embed(
        description: str, title: Optional[str] = "Success"
    ) -> discord.Embed:
        """
        Creates a success embed with a green color.

        :param description: The description of the embed (required).
        :param title: The title of the embed (optional).
        :return: A discord.Embed object.
        """
        return EmbedUtils.create_embed(
            description=description,
            title=title,
            color=discord.Color.green(),
            footer="© 2024 weeaboo",
        )

    @staticmethod
    def error_embed(
        description: str, title: Optional[str] = "An Error has Occured"
    ) -> discord.Embed:
        """
        Creates an error embed with a red color.

        :param description: The description of the embed (required).
        :param title: The title of the embed (optional).
        :return: A discord.Embed object.
        """
        return EmbedUtils.create_embed(
            description=description,
            title=title,
            color=discord.Color.red(),
            footer="© 2025 weeaboo",
        )

    @staticmethod
    def cooldown_embed(remaining_time: float) -> discord.Embed:
        """
        Creates a cooldown embed with information about the remaining time.

        :param remaining_time: The time left for the cooldown in seconds.
        :return: A discord.Embed object.
        """
        description = f"""
        This command is on a cooldown! Please wait **{remaining_time:.1f}s** before using this command!
        """
        return EmbedUtils.create_embed(
            description=description,
            title="Cooldown Active",
            color=discord.Color.yellow(),
            footer="© 2025 weeaboo",
        )


# Example Usage:
# embed = EmbedUtils.create_embed(
#     description="This is an example embed!",
#     title="Welcome",
#     color=discord.Color.green(),
#     fields=[
#         {"name": "Field 1", "value": "Value 1", "inline": False},
#         {"name": "Field 2", "value": "Value 2", "inline": True}
#     ],
#     footer="Footer text",
#     thumbnail_url="https://example.com/thumbnail.png",
#     image_url="https://example.com/image.png",
#     author={"name": "Author Name", "icon_url": "https://example.com/icon.png"}
# )

# success = EmbedUtils.success_embed(description="Operation completed successfully.")
# error = EmbedUtils.error_embed(description="Something went wrong.")
