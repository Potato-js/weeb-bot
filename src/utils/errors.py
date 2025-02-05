from discord.ext import commands


class WeeabooError(commands.CommandError):
    """Raised when a Bot related Errror occurs"""

    pass


class PlayerIsNotAvailable(WeeabooError):
    """Raised when the Lavalink Player is Not connected to a Voice Channel"""

    def __init__(self, message="❗ | The bot isn't connected to a VC", *args):
        super().__init__(message, *args)
